#!/bin/bash
# Daemon script for Smart Strategy V2
# Runs continuously, checking for opportunities every hour

COLOR_GREEN='\033[0;32m'
COLOR_BLUE='\033[0;34m'
COLOR_YELLOW='\033[1;33m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_GREEN}🚀 Smart Strategy V2 - Daemon Mode${COLOR_RESET}"
echo -e "${COLOR_BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
echo ""
echo "Starting continuous monitoring..."
echo "Checking for opportunities every hour"
echo "Will enter trades when Technical Score >= 70"
echo ""
echo -e "${COLOR_YELLOW}Press Ctrl+C to stop${COLOR_RESET}"
echo ""

cd "$(dirname "$0")"

CYCLE=1

while true; do
    echo -e "${COLOR_BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
    echo -e "${COLOR_GREEN}Cycle #$CYCLE - $(date '+%Y-%m-%d %H:%M:%S')${COLOR_RESET}"
    echo -e "${COLOR_BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
    echo ""
    
    # Run strategy
    python3 smart_strategy_v2.py
    
    STATUS=$?
    
    if [ $STATUS -eq 0 ]; then
        echo -e "${COLOR_GREEN}✅ Cycle $CYCLE complete${COLOR_RESET}"
    else
        echo -e "${COLOR_YELLOW}⚠️ Cycle $CYCLE completed with warnings${COLOR_RESET}"
    fi
    
    echo ""
    echo -e "Next scan in 1 hour..."
    echo ""
    
    CYCLE=$((CYCLE + 1))
    
    # Sleep 1 hour
    sleep 3600
done
