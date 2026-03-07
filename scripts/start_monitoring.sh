#!/bin/bash
# NOOGH Performance Monitoring Service
# يعمل في الخلفية ويراقب الأداء كل دقيقة

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Check if already running
if pgrep -f "performance_monitor.py" > /dev/null; then
    echo "⚠️  المراقبة تعمل بالفعل"
    exit 1
fi

# Start monitoring in background
nohup python3 scripts/performance_monitor.py --interval 60 > logs/performance_monitor.log 2>&1 &

echo "✅ بدأت خدمة المراقبة (PID: $!)"
echo "$!" > data/performance_monitor.pid
