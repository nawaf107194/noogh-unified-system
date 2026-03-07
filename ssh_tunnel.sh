#!/bin/bash
# SSH Tunnel to RunPod vLLM
# Maps localhost:9000 → pod:8000

PASS="eu1ckc4krvb4dn66rvll"
HOST="root@213.173.105.10"
PORT=35384

# Kill any existing tunnel on port 9000
fuser -k 9000/tcp 2>/dev/null

echo "🔗 Connecting SSH tunnel to RunPod..."
echo "   Local :9000 → Pod :8000"

# Use ssh with password via stdin redirect
SSH_ASKPASS_REQUIRE=force SSH_ASKPASS="/tmp/ssh_askpass.sh" \
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 \
  -L 9000:localhost:8000 \
  "$HOST" -p $PORT -N -f 2>&1

RET=$?
if [ $RET -eq 0 ]; then
    echo "✅ Tunnel UP! Testing..."
    sleep 1
    curl -s -m 5 http://localhost:9000/v1/models | python3 -m json.tool 2>/dev/null && echo "🧠 vLLM reachable!" || echo "❌ vLLM not responding through tunnel"
else
    echo "❌ SSH failed (exit=$RET)"
fi
