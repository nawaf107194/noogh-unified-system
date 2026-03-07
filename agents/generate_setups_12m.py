#!/usr/bin/env python3
"""
Generate Trading Setups from 12-Month Data
===========================================
Production-grade setup generator with regime tagging
"""

import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading.trap_hybrid_engine import get_trap_hybrid_engine
from trading.regimes import compute_regime_tags, compute_features

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


class SetupGenerator:
    """Generate trading setups from historical data"""

    def __init__(self):
        self.trap_engine = get_trap_hybrid_engine()
        self.data_dir = Path(__file__).parent.parent / 'data'

    def load_parquet_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Load 12-month parquet files"""
        logger.info("📥 Loading 12-month data...")

        micro_file = self.data_dir / "BTCUSDT_5m_12M.parquet"
        macro_file = self.data_dir / "BTCUSDT_1h_12M.parquet"

        if not micro_file.exists() or not macro_file.exists():
            logger.error(f"❌ Parquet files not found!")
            logger.error(f"   Run: python3 src/agents/download_data_12m.py")
            return pd.DataFrame(), pd.DataFrame()

        df_5m = pd.read_parquet(micro_file)
        df_1h = pd.read_parquet(macro_file)

        logger.info(f"✅ Loaded data:")
        logger.info(f"   5m: {len(df_5m):,} candles ({df_5m.index[0]} → {df_5m.index[-1]})")
        logger.info(f"   1h: {len(df_1h):,} candles ({df_1h.index[0]} → {df_1h.index[-1]})")

        return df_5m, df_1h

    def generate_setups(
        self,
        df_5m: pd.DataFrame,
        df_1h: pd.DataFrame
    ) -> List[Dict]:
        """
        Generate setups with regime tags and features

        Args:
            df_5m: 5-minute OHLCV data
            df_1h: 1-hour OHLCV data

        Returns:
            List of setup dictionaries
        """
        logger.info("\n" + "="*70)
        logger.info("🔍 GENERATING SETUPS")
        logger.info("="*70)

        # Compute indicators on 5m data
        logger.info("Computing indicators...")
        df_5m = self.trap_engine.compute_indicators(df_5m)

        logger.info(f"   ATR mean: {df_5m['atr'].mean():.2f}")
        logger.info(f"   Bull sweeps: {df_5m['bull_sweep'].sum()}")
        logger.info(f"   Bear sweeps: {df_5m['bear_sweep'].sum()}")

        setups = []
        last_log = 0

        # Scan for setups (leave 100 bar warmup, 50 bar buffer for outcome)
        for i in range(100, len(df_5m) - 50):
            # Log progress every 10,000 bars
            if i - last_log >= 10000:
                progress = (i / len(df_5m)) * 100
                logger.info(f"   Progress: {progress:.1f}% ({i:,}/{len(df_5m):,})")
                last_log = i

            # Generate signal
            signal = self.trap_engine.generate_signal(df_5m, current_idx=i)

            if signal.signal == 'NONE':
                continue

            # Calculate outcome (50 candles forward)
            entry_price = signal.entry_price
            stop_loss = signal.stop_loss
            take_profit = signal.quick_tp

            future_slice = df_5m.iloc[i+1:i+51]

            hit_tp = False
            hit_sl = False
            max_profit = 0.0
            max_loss = 0.0

            for _, bar in future_slice.iterrows():
                h, l = bar['high'], bar['low']

                if signal.signal == 'LONG':
                    profit_pct = ((h - entry_price) / entry_price) * 100
                    loss_pct = ((l - entry_price) / entry_price) * 100

                    if h >= take_profit:
                        hit_tp = True
                        break
                    if l <= stop_loss:
                        hit_sl = True
                        break

                    max_profit = max(max_profit, profit_pct)
                    max_loss = min(max_loss, loss_pct)

                else:  # SHORT
                    profit_pct = ((entry_price - l) / entry_price) * 100
                    loss_pct = ((entry_price - h) / entry_price) * 100

                    if l <= take_profit:
                        hit_tp = True
                        break
                    if h >= stop_loss:
                        hit_sl = True
                        break

                    max_profit = max(max_profit, profit_pct)
                    max_loss = min(max_loss, loss_pct)

            # Determine outcome
            if hit_tp:
                outcome = 'WIN'
            elif hit_sl:
                outcome = 'LOSS'
            else:
                outcome = 'TIMEOUT'

            # Get regime context (5m slice + 1h slice)
            timestamp = df_5m.index[i]

            # Get 5m slice (last 100 bars for context)
            micro_slice = df_5m.iloc[max(0, i-100):i+1]

            # Get corresponding 1h slice (align by timestamp)
            macro_slice = df_1h[df_1h.index <= timestamp].iloc[-100:]

            # Compute regime tags
            regime_tags = compute_regime_tags(micro_slice, macro_slice)

            # Compute features
            features = compute_features(micro_slice, macro_slice)

            # Get current bar
            bar = df_5m.iloc[i]

            # Build setup dictionary
            setup = {
                'timestamp': str(timestamp),
                'symbol': 'BTCUSDT',
                'signal': signal.signal,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'atr': signal.atr,
                'reasons': signal.reasons,
                'outcome': outcome,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'hit_tp': hit_tp,
                'hit_sl': hit_sl,
                # Basic features
                'rsi': float(bar.get('rsi', 50)),
                'volume': float(bar.get('volume', 0)),
                'taker_buy_ratio': float(bar.get('taker_buy_base', 0) / bar.get('volume', 1)) if bar.get('volume', 0) > 0 else 0.5,
                # Regime tags
                **regime_tags,
                # Advanced features
                **features,
            }

            setups.append(setup)

        logger.info(f"\n✅ Generated {len(setups)} setups")

        # Quick stats
        wins = sum(1 for s in setups if s['outcome'] == 'WIN')
        losses = sum(1 for s in setups if s['outcome'] == 'LOSS')
        timeouts = sum(1 for s in setups if s['outcome'] == 'TIMEOUT')

        wr = (wins / len(setups) * 100) if setups else 0

        logger.info(f"\n📊 Outcome Distribution:")
        logger.info(f"   Wins: {wins} ({wins/len(setups)*100:.1f}%)")
        logger.info(f"   Losses: {losses} ({losses/len(setups)*100:.1f}%)")
        logger.info(f"   Timeouts: {timeouts} ({timeouts/len(setups)*100:.1f}%)")
        logger.info(f"   Win Rate (excl. timeouts): {wr:.1f}%")

        return setups

    def save_setups(self, setups: List[Dict], filename: str = "backtest_setups_12M.jsonl"):
        """Save setups to JSONL file"""
        output_file = self.data_dir / filename

        logger.info(f"\n💾 Saving to: {output_file}")

        with open(output_file, 'w') as f:
            for setup in setups:
                f.write(json.dumps(setup) + '\n')

        size_kb = output_file.stat().st_size / 1024
        logger.info(f"   Size: {size_kb:.2f} KB")
        logger.info(f"   Setups: {len(setups):,}")

        return output_file


def main():
    """Main entry point"""
    logger.info("="*70)
    logger.info("🏛️ SETUP GENERATION - 12 MONTHS")
    logger.info("="*70)

    generator = SetupGenerator()

    # Load data
    df_5m, df_1h = generator.load_parquet_data()

    if df_5m.empty or df_1h.empty:
        logger.error("❌ Failed to load data")
        return

    # Generate setups
    setups = generator.generate_setups(df_5m, df_1h)

    if not setups:
        logger.error("❌ No setups generated")
        return

    # Save
    output_file = generator.save_setups(setups)

    logger.info("\n" + "="*70)
    logger.info("✅ SETUP GENERATION COMPLETE")
    logger.info("="*70)
    logger.info(f"\n📁 Output: {output_file}")
    logger.info(f"🚀 Ready for PSO optimization!\n")


if __name__ == "__main__":
    main()
