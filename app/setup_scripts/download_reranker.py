import os
from huggingface_hub import snapshot_download

local_dir = ".app/models/bge-reranker-v2-m3"
repo_id = "BAAI/bge-reranker-v2-m3"

# Create the directory if it doesn't exist
os.makedirs(local_dir, exist_ok=True)

path = snapshot_download(
    repo_id=repo_id,
    local_dir=local_dir,
    local_dir_use_symlinks=False  # ensures full files are stored, not symlinks
)

print(f"Model snapshot downloaded to: {path}")
