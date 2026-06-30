import os
import re
import torch
import modal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import FastAPI

# 1. Define the container image with PyTorch and Transformers
image = (
    modal.Image.debian_slim()
    .pip_install(
        "torch",
        "transformers",
        "fastapi",
        "pydantic"
    )
)

# 2. Create the Modal App
app = modal.App("contract-qa-server", image=image)

# 3. Create a persistent volume to store the model weights (so we don't have to upload them every time)
volume = modal.Volume.from_name("model-volume", create_if_missing=True)

# Define request/response schemas
class QARequest(BaseModel):
    question: str
    context: str

class QAResponse(BaseModel):
    answer: str
    confidence: float

class QABatchRequest(BaseModel):
    requests: List[QARequest]

class QABatchResponse(BaseModel):
    responses: List[QAResponse]


# 4. Define the Model Class with lifecycle methods
@app.cls(
    cpu=2.0,            # 2 vCPUs
    memory=4096,        # 4GB RAM (enough for roberta-large)
    volumes={"/models": volume}  # Mount the persistent volume at /models
)
class QAinference:
    @modal.enter()
    def load_model(self):
        from transformers import AutoModelForQuestionAnswering, AutoTokenizer
        
        model_path = "/models/roberta-large"
        
        # Fallback to public squad model if local weights aren't uploaded yet
        if not os.path.exists(model_path):
            print(f"⚠️ Local model not found at {model_path} in Volume.")
            print("Falling back to loading 'deepset/roberta-large-squad2' from Hugging Face...")
            model_path = "deepset/roberta-large-squad2"
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
            self.model = AutoModelForQuestionAnswering.from_pretrained(model_path)
        else:
            print(f"✅ Loading local model from Volume: {model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, use_fast=True)
            self.model = AutoModelForQuestionAnswering.from_pretrained(model_path, local_files_only=True)
            
        self.device = torch.device("cpu")
        self.model.to(self.device)
        self.model.eval()

    def _select_best_span(self, input_ids: torch.Tensor, start_logits: torch.Tensor, end_logits: torch.Tensor, context_token_indices: List[int]) -> tuple[str, float]:
        k = min(20, len(context_token_indices))
        if not context_token_indices:
            return "", -999.0

        start_scores = start_logits[context_token_indices]
        end_scores = end_logits[context_token_indices]

        top_start_rel = torch.topk(start_scores, k=k).indices.tolist()
        top_end_rel = torch.topk(end_scores, k=k).indices.tolist()

        top_start = [context_token_indices[i] for i in top_start_rel]
        top_end = [context_token_indices[i] for i in top_end_rel]

        candidates = []
        for s in top_start:
            for e in top_end:
                if e < s or (e - s + 1) > 32:
                    continue
                score = float(start_logits[s] + end_logits[e])
                candidates.append((score, s, e))

        candidates.sort(key=lambda item: item[0], reverse=True)

        for score, s, e in candidates:
            token_slice = input_ids[s : e + 1].tolist()
            answer = self.tokenizer.decode(token_slice, skip_special_tokens=True).strip()
            if answer:
                return answer, score

        return "", -999.0

    def _run_qa_batch(self, items: List[QARequest]) -> List[QAResponse]:
        questions = [item.question for item in items]
        contexts = [item.context for item in items]

        encoded = self.tokenizer(
            questions,
            contexts,
            return_tensors="pt",
            max_length=512,
            truncation="only_second",
            padding=True,
            return_offsets_mapping=True,
        )
        encoded.pop("offset_mapping", None)
        inputs = {k: v.to(self.device) for k, v in encoded.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)

        responses = []
        for i in range(len(items)):
            sequence_ids = encoded.sequence_ids(i)
            context_token_indices = [
                idx for idx, seq_id in enumerate(sequence_ids)
                if seq_id == 1
            ]

            answer, confidence = self._select_best_span(
                input_ids=inputs["input_ids"][i],
                start_logits=outputs.start_logits[i],
                end_logits=outputs.end_logits[i],
                context_token_indices=context_token_indices,
            )
            responses.append(QAResponse(answer=answer, confidence=round(confidence, 2)))

        return responses

    # 5. Expose as web endpoints matching the local API contract
    @modal.web_endpoint(method="POST")
    def qa(self, payload: QARequest) -> QAResponse:
        return self._run_qa_batch([payload])[0]

    @modal.web_endpoint(method="POST")
    def qa_batch(self, payload: QABatchRequest) -> QABatchResponse:
        if not payload.requests:
            return QABatchResponse(responses=[])
        
        # Batch size of 16 for memory efficiency
        all_responses = []
        for start in range(0, len(payload.requests), 16):
            chunk = payload.requests[start:start + 16]
            all_responses.extend(self._run_qa_batch(chunk))
            
        return QABatchResponse(responses=all_responses)
