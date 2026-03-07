#!/bin/bash
cd /home/noogh/projects/noogh_unified_system/src

# Load all environment variables
export NOOGH_PORT=8001
export NOOGH_ADMIN_TOKEN="b7936915e7afef4856b2651c1bec89229af99b9a2dab737689d2c31f8362655b"
export NOOGH_INTERNAL_TOKEN="dev-token-noogh-2026"
export NOOGH_SERVICE_TOKEN="a8827804f6bfef3945a1540f0adb78118be88a8b1cac626578c1c20e7251544c"
export NOOGH_READONLY_TOKEN="c9938a26g8cgfg4a56b27630e1bda89229bf88b8a2dab7376890d3d42f9573766d"
export NOOGH_JOB_SIGNING_SECRET="d0a49b37h9dhgh5b67c38741f2cea90330cg99c9b3ebc84787a0e4e53ga684877e"
export NOOGH_SECRET_KEY="c993e3d47f2c612e3b05a7e0d5168aa70af198281eb802c338becea56758a4fb"
export NOOGH_HOST="0.0.0.0"
export REDIS_URL="redis://localhost:6379/0"
export NEURAL_ENGINE_URL="http://127.0.0.1:8002"
export NOOGH_DATA_DIR="/home/noogh/projects/noogh_unified_system/src/data"
export NOOGH_PROJECT_ROOT="/home/noogh/projects/noogh_unified_system/src"

# Dashboard Control Commands
export NOOGH_NEURAL_START_CMD="/home/noogh/projects/noogh_unified_system/src/start_neural.sh > /tmp/neural_engine.log 2>&1 &"
export NOOGH_NEURAL_STOP_CMD="pkill -f 'neural_engine.api.main'"
export NOOGH_NEURAL_RESTART_CMD="pkill -f 'neural_engine.api.main'; sleep 2; /home/noogh/projects/noogh_unified_system/src/start_neural.sh > /tmp/neural_engine.log 2>&1 &"

# Start Gateway
.venv/bin/python3 -m uvicorn gateway.app.main:app --host 0.0.0.0 --port 8001
