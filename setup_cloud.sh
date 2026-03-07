#!/bin/bash
# ================================================
# NOOGH Cloud Training — Quick Setup Script
# ================================================
# Run this on your cloud GPU instance (RunPod/Vast.ai/Lambda)
#
# Usage:
#   chmod +x setup_cloud.sh
#   ./setup_cloud.sh
# ================================================

set -e

echo "=============================================="
echo "🚀 NOOGH Cloud Training Setup"
echo "=============================================="

# 1. Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -q torch transformers datasets trl peft bitsandbytes accelerate timm

# 2. Login to HuggingFace (for Gemma access)
echo ""
echo "🔑 HuggingFace Login..."
echo "   You need a token from: https://huggingface.co/settings/tokens"
echo "   And Gemma license accepted at: https://huggingface.co/google/gemma-3n-E4B-it"
echo ""
huggingface-cli login

# 3. Verify GPU
echo ""
echo "🎮 GPU Info:"
nvidia-smi --query-gpu=name,memory.total --format=csv
echo ""

# 4. Check dataset exists
if [ -f "NOOGH_V7_EXPANDED.jsonl" ]; then
    SAMPLES=$(wc -l < NOOGH_V7_EXPANDED.jsonl)
    SIZE=$(du -h NOOGH_V7_EXPANDED.jsonl | cut -f1)
    echo "✅ Dataset found: ${SAMPLES} samples (${SIZE})"
else
    echo "❌ Dataset not found!"
    echo "   Upload NOOGH_V7_EXPANDED.jsonl to this directory first."
    exit 1
fi

# 5. Check training script exists
if [ -f "train_cloud.py" ]; then
    echo "✅ Training script found"
else
    echo "❌ train_cloud.py not found!"
    echo "   Upload train_cloud.py to this directory first."
    exit 1
fi

echo ""
echo "=============================================="
echo "🎯 Setup complete! Run training with:"
echo "   python train_cloud.py"
echo "=============================================="
