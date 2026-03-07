#!/bin/bash
# NOOGH Local Execution Startup Script
# Forces NOOGH to use the local Ollama instance and qwen2.5-coder:14b.

cd /home/noogh/projects/noogh_unified_system/src

# Kill any lingering agents
pkill -f agent_daemon

# Set local LLM environment variables
export NEURAL_ENGINE_MODE="vllm"
export NEURAL_ENGINE_URL="http://127.0.0.1:11434"
export VLLM_MODEL_NAME="qwen2.5-coder:14b"
export VLLM_CONTEXT_LENGTH="4096"
export VLLM_MAX_TOKENS="1024"

# Critical NOOGH pathing
export PYTHONPATH="/home/noogh/projects/noogh_unified_system/src:$PYTHONPATH"

# Clear external cloud keys by exporting empty strings so .env does not repopulate them
export RUNPOD_BRAIN_URL=""
export DEEPSEEK_API_KEY=""
export OPENAI_API_KEY=""
export NOOGH_TEACHER_URL="http://127.0.0.1:11434"
export NOOGH_TEACHER_MODE="vllm"
export NOOGH_TEACHER_MODEL="qwen2.5-coder:14b"


echo "========================================================"
echo "🚀 Starting NOOGH in Local Mode"
echo "🧠 Engine: Ollama (Local)"
echo "🤖 Model:  qwen2.5-coder:14b"
echo "========================================================"

# Launch the agent daemon as a module from src root
nohup python3 -m unified_core.agent_daemon > agent_daemon_startup.log 2>&1 &

# Launch the orchestrator
nohup python3 agents/noogh_orchestrator.py > logs/orchestrator.log 2>&1 &
echo "✅ Orchestrator launched."

echo "✅ Agent daemon launched. Run 'tail -f agent_continuous.log' to monitor."
