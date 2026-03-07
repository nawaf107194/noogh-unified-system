#!/bin/bash
cd /home/noogh/projects/noogh_unified_system/src

# Load environment variables
export NOOGH_INTERNAL_TOKEN="dev-token-noogh-2026"
export NOOGH_BACKEND="local-gpu"
export NOOGH_MODEL="unsloth/gemma-3n-E4B-it-bnb-4bit"
export NOOGH_ALLOW_UNSTABLE_BACKEND="true"
export NOOGH_DATA_DIR="/home/noogh/projects/noogh_unified_system/src/data"

# Check if already running
if lsof -i :8002 > /dev/null; then
    echo "⚠️ Neural Engine is already running on port 8002. Aborting."
    exit 1
fi

# Gemma 3n E4B pre-quantized (4-bit NF4) fits in ~5GB VRAM
# RTX 5070 has 12GB — plenty of headroom
export CUDA_VISIBLE_DEVICES="0"
export MAX_MODEL_MEMORY_GB="10"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
.venv/bin/python3 -m uvicorn neural_engine.api.main:app --host 127.0.0.1 --port 8002 --workers 1 --loop asyncio
