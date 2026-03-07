#!/bin/bash
# NOOGH System Startup Script

set -a  # Export all variables
source /home/noogh/projects/noogh_unified_system/src/.env
set +a

echo "Starting NOOGH Neural Engine on port 8002..."
cd /home/noogh/projects/noogh_unified_system/src
/home/noogh/projects/noogh_unified_system/src/.venv/bin/python3 -m uvicorn neural_engine.api.main:app --host 127.0.0.1 --port 8002 > /tmp/neural_engine.log 2>&1 &
NEURAL_PID=$!

sleep 3
echo "Starting NOOGH Gateway on port 8001..."
/home/noogh/projects/noogh_unified_system/src/.venv/bin/python3 -m uvicorn gateway.app.main:app --host 0.0.0.0 --port 8001 > /tmp/gateway.log 2>&1 &
GATEWAY_PID=$!

sleep 2
echo "=== NOOGH System Started ==="
echo "Neural Engine PID: $NEURAL_PID"
echo "Gateway PID: $GATEWAY_PID"
echo ""
echo "Checking health..."
sleep 2
curl -s http://localhost:8002/health && echo " ✓ Neural Engine OK"
curl -s http://localhost:8001/health && echo " ✓ Gateway OK"
