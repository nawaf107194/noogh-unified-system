#!/usr/bin/env python3
"""
تشغيل Autonomous Trading Agent بشكل مستمر
يعمل في loop مع مراقبة الصفقات كل 5 دقائق
"""
import sys
import asyncio
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.autonomous_trading_agent import AutonomousTradingAgent
from unified_core.neural_bridge import NeuralEngineClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """تشغيل مستمر مع monitoring"""

    print("\n" + "="*80)
    print("🚀 Starting Autonomous Trading Agent - CONTINUOUS MODE")
    print("="*80)

    # Initialize Neural Bridge
    neural_bridge = NeuralEngineClient(
        base_url="http://localhost:11434",
        mode="vllm"
    )

    # Initialize Agent in OBSERVE mode
    agent = AutonomousTradingAgent(
        mode='observe',  # ✅ OBSERVATION ONLY - No real trades, no paper engine fills
        testnet=True,    # Use testnet data for safety
        neural_bridge=neural_bridge
    )

    await agent.initialize()

    print("\n✅ Agent initialized successfully!")
    print(f"   Mode: OBSERVE (Monitoring only, no executions)")
    print(f"   Network: TESTNET")
    print(f"   Symbols: {len(agent.symbols)}")
    print(f"   Cycle Interval: 5 minutes")
    print("\n" + "="*80)
    print("Agent is now running... Press Ctrl+C to stop")
    print("="*80 + "\n")

    # Continuous loop
    cycle_count = 0
    try:
        while True:
            cycle_count += 1

            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 Cycle #{cycle_count}")
            logger.info(f"{'='*60}")

            # Run one cycle
            await agent.run_cycle()

            # Display performance every 10 cycles
            if cycle_count % 10 == 0:
                insights = await agent.get_learning_insights()
                perf = insights['performance']

                logger.info(f"\n📊 Performance Summary (Cycle {cycle_count}):")
                logger.info(f"   Total Trades: {perf['total_trades']}")
                logger.info(f"   Win Rate: {perf['win_rate']:.1f}%")
                logger.info(f"   Balance: ${perf['balance']:.2f}")
                logger.info(f"   ROI: {perf['roi']:+.2f}%")
                logger.info(f"   Open Positions: {insights['open_positions']}")

            # Wait 5 minutes before next cycle
            logger.info(f"\n⏳ Waiting 5 minutes before next cycle...")
            await asyncio.sleep(300)  # 5 minutes

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Shutting down agent...")

        # Final performance report
        insights = await agent.get_learning_insights()
        perf = insights['performance']

        print("\n" + "="*80)
        print("📊 FINAL PERFORMANCE REPORT")
        print("="*80)
        print(f"Total Cycles: {cycle_count}")
        print(f"Total Trades: {perf['total_trades']}")
        print(f"Wins: {perf.get('wins', 0)} | Losses: {perf.get('losses', 0)}")
        print(f"Win Rate: {perf['win_rate']:.1f}%")
        print(f"Balance: ${perf['balance']:.2f}")
        print(f"ROI: {perf['roi']:+.2f}%")
        print(f"Open Positions: {insights['open_positions']}")
        print("="*80)
        print("✅ Agent stopped successfully")
        print("="*80 + "\n")

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
