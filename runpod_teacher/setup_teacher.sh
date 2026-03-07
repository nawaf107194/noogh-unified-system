#!/bin/bash
# =====================================================
# NOOGH Teacher Model Setup - RunPod A100 80GB
# Deploys Qwen 2.5 32B as OpenAI-compatible API
# =====================================================
# Usage:
#   On RunPod terminal:
#   bash setup_teacher.sh
#   python3 /workspace/run_teacher.py
# =====================================================

set -e

echo "🧠 NOOGH Teacher Model - Setting up Qwen 32B on A100..."

# Install vLLM
pip install -q vllm openai

# Create API server script
cat > /workspace/run_teacher.py << 'PYEOF'
#!/usr/bin/env python3
"""
NOOGH Teacher API - Qwen 2.5 32B Instruct
Runs as OpenAI-compatible API endpoint on port 8000.
Optimized for A100 80GB.
"""
import subprocess
import sys

# === MODEL OPTIONS ===
# Option A: Qwen 32B Full Precision (needs ~65GB VRAM)
# MODEL = "Qwen/Qwen2.5-32B-Instruct"
# QUANTIZATION = None

# Option B: Qwen 32B AWQ (needs ~20GB VRAM, fast)
MODEL = "Qwen/Qwen2.5-32B-Instruct-AWQ"
QUANTIZATION = "awq"

# Option C: Qwen 72B AWQ (needs ~45GB VRAM)
# MODEL = "Qwen/Qwen2.5-72B-Instruct-AWQ"
# QUANTIZATION = "awq"

cmd = [
    sys.executable, "-m", "vllm.entrypoints.openai.api_server",
    "--model", MODEL,
    "--host", "0.0.0.0",
    "--port", "8000",
    "--max-model-len", "8192",     # A100 can handle 8K context
    "--tensor-parallel-size", "1", # Single GPU
    "--gpu-memory-utilization", "0.92",
    "--trust-remote-code",
    "--served-model-name", "noogh-teacher",
    "--download-dir", "/workspace/models",
]

if QUANTIZATION:
    cmd.extend(["--quantization", QUANTIZATION])

print(f"🚀 Starting Teacher API: {MODEL}")
print(f"   Port: 8000")
print(f"   Context: 8192 tokens")
print(f"   VRAM Utilization: 92%")
print(f"   Quantization: {QUANTIZATION or 'None (full precision)'}")
print(f"   Endpoint: http://0.0.0.0:8000/v1/chat/completions")
print(f"   Proxy: https://<POD_ID>-8000.proxy.runpod.net")

subprocess.run(cmd)
PYEOF

chmod +x /workspace/run_teacher.py

echo "✅ Setup complete!"
echo ""
echo "📋 To start the teacher API:"
echo "   python3 /workspace/run_teacher.py"
echo ""
echo "📋 API will be available at:"
echo "   Local:  http://localhost:8000/v1/chat/completions"
echo "   Proxy:  https://<POD_ID>-8000.proxy.runpod.net/v1/chat/completions"
echo ""
echo "📋 To test from your local machine:"
echo "   python3 src/runpod_teacher/connect_brain.py --pod-id <POD_ID>"
