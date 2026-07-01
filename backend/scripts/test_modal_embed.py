import urllib.request
import json
import sys
import os
from pathlib import Path

# Load env variables
backend_dir = Path(__file__).resolve().parent.parent
repo_root = backend_dir.parent
try:
    from dotenv import load_dotenv
    load_dotenv(repo_root / ".env")
except Exception:
    pass

url = os.getenv("MODEL_SERVER_URL", "").strip()
if not url:
    print("Error: MODEL_SERVER_URL not found in .env")
    sys.exit(1)

# Standardize path
url = url.rstrip("/")
if not url.endswith("/embed"):
    url += "/embed"

print(f"Testing Modal Embed URL: {url}")

payload = json.dumps({"texts": ["Hello world", "Test sentence for embedding"]}).encode("utf-8")
req = urllib.request.Request(
    url,
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=10.0) as response:
        res = json.loads(response.read().decode("utf-8"))
        embeddings = res.get("embeddings", [])
        print(f"Success! Received {len(embeddings)} embeddings.")
        print(f"Dimension: {len(embeddings[0]) if embeddings else 'N/A'}")
except Exception as e:
    print(f"Failed: {e}")
    if hasattr(e, "read"):
        try:
            print(e.read().decode("utf-8"))
        except Exception:
            pass
