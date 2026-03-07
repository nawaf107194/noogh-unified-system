#!/usr/bin/env python3
"""
Monitor-Only Mode - لمراقبة الصفقات المفتوحة فقط بدون فتح صفقات جديدة
"""
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.autonomous_trading_agent import AutonomousTradingAgent
from unified_core.neural_bridge import NeuralEngineClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """مراقبة الصفقات المفتوحة فقط - لا يفتح صفقات جديدة"""

    print("\n" + "="*80)
    print("🔍 MONITOR-ONLY MODE - Position Monitoring")
    print("="*80)
    print("⚠️  Agent will:")
    print("   - Recover open positions from Binance")
    print("   - Monitor SL/TP every cycle")
    print("   - Auto-close positions when triggered")
    print("   - NOT open new trades")
    print("="*80 + "\n")

    # Initialize Neural Bridge (optional for monitoring)
    neural_bridge = NeuralEngineClient(
        base_url="http://localhost:11434",
        mode="vllm"
    )

    # Initialize Agent in HYBRID mode
    agent = AutonomousTradingAgent(
        mode='hybrid',
        neural_bridge=neural_bridge
    )

    await agent.initialize()

    print(f"\n✅ Agent initialized")
    print(f"   Mode: Hybrid (Monitor-only)")
    print(f"   Positions recovered: {len(agent.trap_trader.positions)}")
    print("="*80 + "\n")

    if not agent.trap_trader.positions:
        print("⚠️  No open positions to monitor!")
        print("   Exiting monitor-only mode.\n")
        return

    # Display recovered positions
    print("📊 Monitoring these positions:\n")
    for symbol, pos in agent.trap_trader.positions.items():
        print(f"   {symbol}:")
        print(f"      Side: {pos.side}")
        print(f"      Entry: ${pos.entry_price:.4f}")
        print(f"      Stop Loss: ${pos.stop_loss:.4f}")
        print(f"      Quick TP: ${pos.quick_tp:.4f}")
        print(f"      Qty: {pos.qty_quick + pos.qty_trail:.2f}")
        print()

    print("="*80)
    print("🔄 Starting monitor loop (every 60 seconds)...")
    print("   Press Ctrl+C to stop")
    print("="*80 + "\n")

    # Monitor loop
    cycle = 0
    try:
        while agent.trap_trader.positions:
            cycle += 1
            logger.info(f"{'='*60}")
            logger.info(f"Monitor Cycle #{cycle} - {datetime.now().strftime('%H:%M:%S')}")
            logger.info(f"{'='*60}")

            # Monitor positions only (no new trades)
            await agent.monitor_paper_positions()

            # Check if any positions left
            if not agent.trap_trader.positions:
                logger.info("\n✅ All positions closed!")
                break

            logger.info(f"   ⏳ Waiting 60 seconds before next check...")
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Stopping monitor...")

    # Final report
    print("\n" + "="*80)
    print("📊 FINAL STATUS")
    print("="*80)

    if agent.trap_trader.positions:
        print(f"⚠️  {len(agent.trap_trader.positions)} positions still open:")
        for symbol in agent.trap_trader.positions.keys():
            print(f"   - {symbol}")
        print("\n   These positions will continue on Binance.")
        print("   Restart this script to continue monitoring.")
    else:
        print("✅ All positions closed successfully!")

    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
