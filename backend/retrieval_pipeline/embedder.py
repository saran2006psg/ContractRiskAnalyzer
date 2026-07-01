"""
Embedding generation module for Legal Contract Risk Analyzer.

This module provides functionality to generate embeddings for contract clauses
using SentenceTransformer models, with singleton model loading for efficiency.
"""

import logging
from typing import List, Union

import numpy as np

import json
import urllib.request
import urllib.error
import os

# We no longer import SentenceTransformer globally.
# This prevents PyTorch and SentenceTransformers from being loaded into memory
# when running on lightweight production platforms like Render's Free tier.

from .config import (
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    NORMALIZE_EMBEDDINGS,
    BATCH_SIZE,
    MODEL_SERVER_URL,
)

logger = logging.getLogger(__name__)

# Module-level variable for singleton model instance (only used locally)
_model_instance = None


def _load_model():
    """
    Load the SentenceTransformer model locally (singleton pattern).
    Only called as a fallback if no remote model server is configured.
    """
    global _model_instance
    
    if _model_instance is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for local embedding generation. "
                "Install it with: pip install sentence-transformers"
            )
            
        logger.info(f"Loading embedding model locally: {EMBEDDING_MODEL}")
        _model_instance = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"Model loaded successfully (dimension: {EMBEDDING_DIMENSION})")
    
    return _model_instance


def _embed_remotely(texts: List[str]) -> Optional[List[List[float]]]:
    """Generate embeddings using the remote Modal serverless endpoint."""
    if not MODEL_SERVER_URL:
        return None
        
    try:
        # Standardize endpoint path to /embed
        url = MODEL_SERVER_URL.rstrip("/")
        if not url.endswith("/embed"):
            url += "/embed"
            
        payload = json.dumps({"texts": texts}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        logger.info(f"Requesting {len(texts)} embeddings remotely from: {url}")
        with urllib.request.urlopen(req, timeout=15.0) as response:
            res = json.loads(response.read().decode("utf-8"))
            
        embeddings = res.get("embeddings", [])
        if embeddings and len(embeddings) == len(texts):
            return embeddings
    except Exception as e:
        logger.warning("Failed to get remote embeddings from Modal: %s. Falling back to local.", e)
        
    return None


def embed_clause(clause: str) -> List[float]:
    """
    Generate an embedding vector for a single contract clause.
    
    Args:
        clause: Text of the contract clause
        
    Returns:
        Embedding vector as a list of floats (length = 768)
        
    Raises:
        ValueError: If the clause is empty or None
        
    Example:
        >>> clause = "The term of this agreement shall be 12 months."
        >>> vector = embed_clause(clause)
        >>> len(vector)
        768
    """
    if not clause or not clause.strip():
        raise ValueError("Clause text cannot be empty")
        
    # 1. Try remote Modal endpoint first
    remote_res = _embed_remotely([clause])
    if remote_res:
        return remote_res[0]
        
    # 2. Local fallback
    model = _load_model()
    embedding = model.encode(
        clause,
        normalize_embeddings=NORMALIZE_EMBEDDINGS,
        show_progress_bar=False
    )
    return embedding.tolist()


def embed_clauses(clauses: List[str], show_progress: bool = True) -> List[List[float]]:
    """
    Generate embedding vectors for multiple contract clauses (batch processing).
    
    This function is more efficient than calling embed_clause() multiple times
    as it processes clauses in batches.
    
    Args:
        clauses: List of contract clause texts
        show_progress: Whether to display a progress bar during encoding
        
    Returns:
        List of embedding vectors, each as a list of floats
        
    Raises:
        ValueError: If clauses list is empty or contains only empty strings
        
    Example:
        >>> clauses = [
        ...     "The term shall be 12 months.",
        ...     "Either party may terminate with 30 days notice.",
        ...     "This agreement is governed by New York law."
        ... ]
        >>> vectors = embed_clauses(clauses)
        >>> len(vectors)
        3
        >>> len(vectors[0])
        768
    """
    if not clauses:
        raise ValueError("Clauses list cannot be empty")
    
    # Filter out empty clauses
    valid_clauses = [c for c in clauses if c and c.strip()]
    
    if not valid_clauses:
        raise ValueError("All clauses are empty")
    
    if len(valid_clauses) < len(clauses):
        logger.warning(
            f"Filtered out {len(clauses) - len(valid_clauses)} empty clause(s)"
        )
    
    logger.info(f"Generating embeddings for {len(valid_clauses)} clause(s)")
    
    # 1. Try remote Modal endpoint first
    remote_res = _embed_remotely(valid_clauses)
    if remote_res:
        return remote_res
        
    # 2. Local fallback
    model = _load_model()
    embeddings = model.encode(
        valid_clauses,
        batch_size=BATCH_SIZE,
        normalize_embeddings=NORMALIZE_EMBEDDINGS,
        show_progress_bar=show_progress
    )
    return embeddings.tolist()


def get_embedding_dimension() -> int:
    """
    Get the dimension of embeddings produced by the model.
    
    Returns:
        Embedding dimension (768 for all-mpnet-base-v2)
        
    Example:
        >>> get_embedding_dimension()
        768
    """
    return EMBEDDING_DIMENSION


def reset_model_cache():
    """
    Reset the cached model instance (useful for testing or memory management).
    
    This forces the model to be reloaded on the next embedding operation.
    """
    global _model_instance
    _model_instance = None
    logger.info("Model cache cleared")
