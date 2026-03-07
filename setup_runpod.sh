#!/bin/bash
# ================================================
# NOOGH Research Agent — RunPod Quick Setup
# ================================================
# Run this on your RunPod GPU pod
#
# Usage:
#   chmod +x setup_runpod.sh && ./setup_runpod.sh
# ================================================

set -e

echo "=============================================="
echo "🚀 NOOGH Research Agent — RunPod Setup"
echo "=============================================="

# 1. Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -q torch transformers datasets trl peft bitsandbytes accelerate

# 2. Verify GPU
echo ""
echo "🎮 GPU Info:"
nvidia-smi --query-gpu=name,memory.total,temperature.gpu --format=csv
echo ""

# 3. Check dataset
if [ -f "NOOGH_RESEARCH_AGENT_V1.jsonl" ]; then
    SAMPLES=$(wc -l < NOOGH_RESEARCH_AGENT_V1.jsonl)
    SIZE=$(du -h NOOGH_RESEARCH_AGENT_V1.jsonl | cut -f1)
    echo "✅ Dataset: ${SAMPLES} samples (${SIZE})"
else
    echo "❌ Dataset not found!"
    echo "   Upload NOOGH_RESEARCH_AGENT_V1.jsonl first."
    echo ""
    echo "   From your local machine:"
    echo "   runpodctl send NOOGH_RESEARCH_AGENT_V1.jsonl"
    echo "   OR"
    echo "   scp NOOGH_RESEARCH_AGENT_V1.jsonl root@<POD_IP>:/workspace/"
    exit 1
fi

# 4. Check training script
if [ -f "train_qwen_runpod.py" ]; then
    echo "✅ Training script found"
else
    echo "❌ train_qwen_runpod.py not found!"
    exit 1
fi

# 5. Test imports
echo ""
echo "🧪 Testing imports..."
python3 -c "
import torch
from transformers import AutoTokenizer
from peft import LoraConfig
from trl import SFTTrainer
print(f'✅ PyTorch {torch.__version__}')
print(f'✅ CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✅ GPU: {torch.cuda.get_device_name(0)}')
    print(f'✅ VRAM: {torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB')
"

echo ""
echo "=============================================="
echo "🎯 Ready! Start training with:"
echo "   python train_qwen_runpod.py"
echo "=============================================="
