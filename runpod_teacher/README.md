# NOOGH Teacher — RunPod A100 Integration

## 🧠 Overview

This module connects the local NOOGH system to a remote **Qwen 2.5 32B** model
running on RunPod A100 80GB via vLLM.

```
[Local Machine]                    [RunPod A100 80GB]
├── Agent Daemon ──HTTP──→ vLLM (Qwen 32B on port 8000)
├── Redis                         └── noogh-teacher model
├── Gateway
└── Neural Bridge (vllm mode)
```

## 🚀 Quick Start

### Step 1: Set up RunPod
1. Create a RunPod pod with A100 80GB GPU
2. Open the pod terminal
3. Upload `setup_teacher.sh` or copy-paste its contents
4. Run:
```bash
bash setup_teacher.sh
python3 /workspace/run_teacher.py
```
5. Wait for the model to download and load (first time: ~10min)
6. Note your Pod ID (from the URL or pod settings)

### Step 2: Connect Local NOOGH
```bash
# From your local machine
cd /home/noogh/projects/noogh_unified_system

# Test connection
python3 src/runpod_teacher/connect_brain.py --pod-id YOUR_POD_ID

# If successful, run the system
export NEURAL_ENGINE_URL=https://YOUR_POD_ID-8000.proxy.runpod.net
export NEURAL_ENGINE_MODE=vllm
export VLLM_MODEL_NAME=noogh-teacher
python3 -m unified_core.agent_daemon
```

### Step 3: Collect Training Data (Optional)
```bash
# Run on the RunPod pod itself (localhost, fastest)
python3 run_on_pod.py
```

## 📁 Files

| File | Purpose |
|------|---------|
| `setup_teacher.sh` | Sets up vLLM + Qwen 32B on RunPod |
| `connect_brain.py` | Tests connection from local → RunPod |
| `run_on_pod.py` | Trajectory recorder (runs on RunPod) |
| `trajectory_recorder.py` | Extended trajectory recorder |
| `../../config/runpod_brain.env` | Environment config |

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEURAL_ENGINE_URL` | `http://127.0.0.1:8002` | Neural Engine URL |
| `NEURAL_ENGINE_MODE` | `local` | `local` or `vllm` |
| `VLLM_MODEL_NAME` | `noogh-teacher` | Model name in vLLM |
| `VLLM_MAX_TOKENS` | `4096` | Max output tokens |
| `VLLM_TEMPERATURE` | `0.7` | Generation temperature |
| `NEURAL_TIMEOUT_SECONDS` | `180` | Request timeout |
| `NEURAL_MAX_RETRIES` | `3` | Retry count for vLLM |

## 🔄 Switching Between Modes

### Use RunPod (vLLM):
```bash
export NEURAL_ENGINE_URL=https://POD_ID-8000.proxy.runpod.net
export NEURAL_ENGINE_MODE=vllm
```

### Use Local Neural Engine:
```bash
export NEURAL_ENGINE_URL=http://127.0.0.1:8002
export NEURAL_ENGINE_MODE=local
```
