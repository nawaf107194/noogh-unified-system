#!/bin/bash
# Quick helper to stop NOOGH services

echo "🛑 Stopping NOOGH Services..."

# Kill Gateway
pkill -f "gateway.app.main" && echo "✅ Stopped Gateway" || echo "⚠️  Gateway not running"

# Kill Worker  
pkill -f "gateway.app.core.worker" && echo "✅ Stopped Worker" || echo "⚠️  Worker not running"

# Optional: Stop Redis if started by us
if docker ps | grep -q noogh-redis; then
    docker stop noogh-redis > /dev/null 2>&1
    docker rm noogh-redis > /dev/null 2>&1
    echo "✅ Stopped Redis (Docker)"
fi

echo ""
echo "✅ All services stopped"
