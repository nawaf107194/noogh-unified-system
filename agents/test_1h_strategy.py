#!/usr/bin/env python3
"""
Quick Test: 1H Liquidity Strategy
==================================
Test new strategy on BTCUSDT 1h data to see if it has edge
"""

import sys
import json
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading.liquidity_1h_strategy import get_liquidity_1h_strategy


def test_strategy():
    """Quick test of 1H strategy"""

    print("="*70)
    print("🔬 TESTING 1H LIQUIDITY STRATEGY")
    print("="*70)

    # Load 1h data
    data_file = Path(__file__).parent.parent / 'data' / 'BTCUSDT_1h_12M.parquet'

    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return

    df = pd.read_parquet(data_file)
    print(f"\n✅ Loaded {len(df):,} 1h candles")
    print(f"   Date range: {df.index[0]} → {df.index[-1]}")

    # Initialize strategy
    strategy = get_liquidity_1h_strategy()

    # Compute indicators
    df = strategy.compute_indicators(df)

    print(f"\n🔍 Scanning for setups...")

    # Scan for signals
    setups = []

    for i in range(100, len(df) - 12):  # Leave 12h buffer for outcome
        signal = strategy.generate_signal(df, i)

        if signal.signal == 'NONE':
            continue

        # Evaluate outcome (next 12 candles = 12 hours)
        entry = signal.entry_price
        sl = signal.stop_loss
        tp = signal.take_profit

        future = df.iloc[i+1:i+13]

        hit_tp = False
        hit_sl = False

        for _, bar in future.iterrows():
            if signal.signal == 'LONG':
                if bar['high'] >= tp:
                    hit_tp = True
                    break
                if bar['low'] <= sl:
                    hit_sl = True
                    break
            else:  # SHORT
                if bar['low'] <= tp:
                    hit_tp = True
                    break
                if bar['high'] >= sl:
                    hit_sl = True
                    break

        outcome = 'WIN' if hit_tp else ('LOSS' if hit_sl else 'TIMEOUT')

        setup = {
            'timestamp': str(df.index[i]),
            'signal': signal.signal,
            'entry_price': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'outcome': outcome,
            'reasons': signal.reasons,
            'confidence': signal.confidence,
            'trend_4h': signal.trend_4h,
        }

        setups.append(setup)

    print(f"\n✅ Found {len(setups)} setups")

    if len(setups) == 0:
        print("⚠️  No setups found - strategy may be too restrictive")
        return

    # Calculate metrics
    wins = sum(1 for s in setups if s['outcome'] == 'WIN')
    losses = sum(1 for s in setups if s['outcome'] == 'LOSS')
    timeouts = sum(1 for s in setups if s['outcome'] == 'TIMEOUT')

    print(f"\n📊 RAW PERFORMANCE:")
    print(f"   Wins: {wins}")
    print(f"   Losses: {losses}")
    print(f"   Timeouts: {timeouts}")

    if losses > 0:
        pf = wins / losses
        wr = (wins / (wins + losses)) * 100
        print(f"   Win Rate: {wr:.1f}%")
        print(f"   Profit Factor: {pf:.2f}")

    # Show some examples
    print(f"\n📋 Sample Setups:")
    for setup in setups[:5]:
        print(f"   {setup['timestamp']} | {setup['signal']} | {setup['outcome']} | {setup['reasons']}")

    # Save for detailed analysis
    output = Path(__file__).parent.parent / 'data' / 'test_1h_setups.jsonl'
    with open(output, 'w') as f:
        for setup in setups:
            f.write(json.dumps(setup) + '\n')

    print(f"\n💾 Saved detailed results to: {output.name}")

    print(f"\n{'='*70}")

    # Verdict
    if losses > 0:
        if pf >= 1.3:
            print("✅ PROMISING - PF ≥ 1.3 - Worth full validation")
        elif pf >= 1.1:
            print("⚠️  WEAK SIGNAL - PF 1.1-1.3 - Needs refinement")
        else:
            print("❌ NO EDGE - PF < 1.1 - Strategy fails")

    print("="*70)


if __name__ == "__main__":
    test_strategy()
