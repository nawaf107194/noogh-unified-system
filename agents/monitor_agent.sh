#!/bin/bash
# مراقبة Autonomous Trading Agent في الوقت الفعلي

LOG_FILE="/home/noogh/projects/noogh_unified_system/src/logs/autonomous_trading_agent.log"

echo "═══════════════════════════════════════════════════════════════"
echo "📊 Autonomous Trading Agent - Live Monitor"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if agent is running
if pgrep -f "autonomous_trading_agent" > /dev/null; then
    PID=$(pgrep -f "autonomous_trading_agent")
    echo "✅ Agent Running (PID: $PID)"
else
    echo "❌ Agent NOT running"
    exit 1
fi

# Extract key info from last 100 lines
echo ""
echo "📋 Recent Activity:"
echo "─────────────────────────────────────────────────────────────"

# Mode
MODE=$(tail -200 "$LOG_FILE" | grep "AutonomousTradingAgent initialized" | tail -1 | grep -o "Mode: [a-z]*" | tail -1)
echo "Mode: $MODE"

# Balance
BALANCE=$(tail -200 "$LOG_FILE" | grep "Futures Balance" | tail -1 | grep -o '\$[0-9.]*')
echo "Balance: $BALANCE"

# Cycle count
CYCLE=$(tail -200 "$LOG_FILE" | grep "Trading Cycle" | tail -1 | grep -o "Cycle [0-9]*")
echo "Current: $CYCLE"

echo ""
echo "🔍 Recent Signals:"
echo "─────────────────────────────────────────────────────────────"
tail -100 "$LOG_FILE" | grep "Signal detected" | tail -5

echo ""
echo "🧠 Brain Decisions:"
echo "─────────────────────────────────────────────────────────────"
tail -100 "$LOG_FILE" | grep "Brain Decision" | tail -5

echo ""
echo "📊 Potential Setups Found:"
echo "─────────────────────────────────────────────────────────────"
tail -100 "$LOG_FILE" | grep "Found .* potential setups" | tail -5

echo ""
echo "⚠️  Warnings/Errors:"
echo "─────────────────────────────────────────────────────────────"
tail -100 "$LOG_FILE" | grep -E "WARNING|ERROR" | tail -5

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Commands:"
echo "  • Live tail: tail -f $LOG_FILE"
echo "  • Stop agent: pkill -f autonomous_trading_agent"
echo "  • Restart: python3 -m src.agents.autonomous_trading_agent"
echo "═══════════════════════════════════════════════════════════════"
