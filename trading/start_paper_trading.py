#!/usr/bin/env python3
"""
Paper Trading Bot - Start Here!
Runs Trap Hybrid Strategy in paper trading mode

Usage:
    python3 -m src.trading.start_paper_trading

Press Ctrl+C to stop
"""
import time
import logging
from datetime import datetime
from trading.trap_live_trader import TrapLiveTrader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('paper_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    print("\n" + "="*80)
    print("          🚀 TRAP HYBRID STRATEGY - PAPER TRADING BOT")
    print("="*80)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: PAPER TRADING (Safe - No real money)")
    print(f"Strategy: Hybrid Exit (64.6% WR, PF 1.12)")
    print(f"\nSymbols: BTCUSDT")
    print(f"Check Interval: 5 minutes")
    print(f"Risk: 1% per trade")
    print(f"\nPress Ctrl+C to stop")
    print("="*80 + "\n")

    # Initialize trader
    trader = TrapLiveTrader(
        testnet=True,
        read_only=True,  # Paper trading
        risk_per_trade=0.01,
        initial_capital=10_000.0
    )

    symbols = ['BTCUSDT']

    # Stats
    checks = 0
    signals_found = 0
    positions_opened = 0

    try:
        while True:
            checks += 1
            logger.info(f"Check #{checks} - Scanning {len(symbols)} symbols...")

            # Check each symbol
            for symbol in symbols:
                try:
                    # Check for signal
                    signal = trader.check_signal(symbol)

                    if signal.signal != 'NONE':
                        signals_found += 1
                        logger.info(f"🎯 SIGNAL: {signal.signal} {symbol}")
                        logger.info(f"   Entry: ${signal.entry_price:.2f}")
                        logger.info(f"   Stop: ${signal.stop_loss:.2f}")
                        logger.info(f"   Quick TP: ${signal.quick_tp:.2f}")

                        # Execute
                        result = trader.execute_signal(signal, symbol)

                        if result['success']:
                            positions_opened += 1
                            logger.info(f"   ✅ Position opened (Paper)")
                        else:
                            logger.warning(f"   ⚠️ Failed: {result['message']}")

                except Exception as e:
                    logger.error(f"Error checking {symbol}: {e}")

            # Monitor active positions
            try:
                status = trader.monitor_positions()

                if status.get('exits'):
                    for exit_event in status['exits']:
                        logger.info(f"🚪 EXIT: {exit_event['reason']} {exit_event['symbol']}")
                        logger.info(f"   Price: ${exit_event['price']:.2f}")
                        logger.info(f"   PNL: ${exit_event['pnl']:.2f}")

            except Exception as e:
                logger.error(f"Error monitoring positions: {e}")

            # Status update
            trader_status = trader.get_status()
            logger.info(f"Status: {trader_status['active_positions']} active positions")
            logger.info(f"Stats: {signals_found} signals, {positions_opened} positions opened")

            # Wait 5 minutes
            logger.info(f"Waiting 5 minutes... (Next check: {datetime.now().strftime('%H:%M')})")
            time.sleep(300)

    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("          📊 PAPER TRADING SESSION ENDED")
        print("="*80)
        print(f"\nDuration: {checks * 5} minutes ({checks} checks)")
        print(f"Signals Found: {signals_found}")
        print(f"Positions Opened: {positions_opened}")
        print(f"\nLog file: paper_trading.log")
        print("\nGoodbye! 👋")
        print("="*80 + "\n")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        print("Check paper_trading.log for details")


if __name__ == "__main__":
    main()
