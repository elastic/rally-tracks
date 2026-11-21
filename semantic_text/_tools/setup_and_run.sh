#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Installing system deps (ICU for PyICU) ==="
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq libicu-dev pkg-config
fi

echo "=== Installing Python deps ==="
pip install --upgrade pip
pip install -r requirements.txt

# Optional: flash-attn for speed. May fail on some envs; fine to skip.
pip install flash-attn --no-build-isolation 2>/dev/null || \
    echo "flash-attn install failed, using default attention"

echo "=== Pre-downloading model ==="
hf download jinaai/jina-embeddings-v5-text-small

echo "=== Pre-downloading BEIR/dbpedia-entity corpus ==="
hf download BeIR/dbpedia-entity --repo-type dataset

echo "=== Verifying GPU ==="
nvidia-smi
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0)}')"

echo "=== Running embedding generation ==="
python3 "$SCRIPT_DIR/generate_beir_embeddings.py"

echo "=== All done ==="
