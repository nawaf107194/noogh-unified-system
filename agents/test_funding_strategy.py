#!/usr/bin/env python3
"""
Test Funding Rate Strategy
============================
Test funding rate mean reversion on BTCUSDT data
"""

import sys
import json
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading.funding_rate_strategy import get_funding_rate_strategy


def test_strategy():
    """Test Funding Rate strategy"""

    print("="*70)
    print("🔬 TESTING FUNDING RATE STRATEGY")
    print("="*70)

    # Load data with funding rates
    data_file = Path(__file__).parent.parent / 'data' / 'BTCUSDT_1h_with_funding_12M.parquet'

    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        print(f"💡 Run download_funding_data.py first")
        return

    df = pd.read_parquet(data_file)
    print(f"\n✅ Loaded {len(df):,} 1h candles with funding rates")
    print(f"   Date range: {df.index[0]} → {df.index[-1]}")

    # Check for funding_rate column
    if 'funding_rate' not in df.columns:
        print(f"❌ No 'funding_rate' column in data")
        print(f"   Available columns: {list(df.columns)}")
        return

    # Quick funding stats
    print(f"\n📊 Funding Rate Stats:")
    print(f"   Mean: {df['funding_rate'].mean()*100:.4f}%")
    print(f"   Median: {df['funding_rate'].median()*100:.4f}%")
    print(f"   P10: {df['funding_rate'].quantile(0.10)*100:.4f}%")
    print(f"   P90: {df['funding_rate'].quantile(0.90)*100:.4f}%")
    print(f"   Min: {df['funding_rate'].min()*100:.4f}%")
    print(f"   Max: {df['funding_rate'].max()*100:.4f}%")

    # Initialize strategy
    strategy = get_funding_rate_strategy()

    # Compute indicators
    print(f"\n🔧 Computing indicators...")
    df = strategy.compute_indicators(df)

    print(f"\n🔍 Scanning for setups...")

    # Scan for signals
    setups = []

    for i in range(strategy.lookback_days * 3 + 100, len(df) - strategy.max_hold_hours):
        signal = strategy.generate_signal(df, i)

        if signal.signal == 'NONE':
            continue

        # Evaluate outcome (next max_hold_hours = 7 days max)
        entry = signal.entry_price
        sl = signal.stop_loss
        tp = signal.take_profit

        future = df.iloc[i+1:i+strategy.max_hold_hours+1]

        hit_tp = False
        hit_sl = False
        exit_idx = None
        exit_reason = None

        for j, (ts, bar) in enumerate(future.iterrows()):
            # Check TP/SL
            if signal.signal == 'LONG':
                if bar['high'] >= tp:
                    hit_tp = True
                    exit_idx = j + 1
                    exit_reason = 'TP'
                    break
                if bar['low'] <= sl:
                    hit_sl = True
                    exit_idx = j + 1
                    exit_reason = 'SL'
                    break
            else:  # SHORT
                if bar['low'] <= tp:
                    hit_tp = True
                    exit_idx = j + 1
                    exit_reason = 'TP'
                    break
                if bar['high'] >= sl:
                    hit_sl = True
                    exit_idx = j + 1
                    exit_reason = 'SL'
                    break

            # Check funding normalization (exit condition)
            if not pd.isna(bar.get('funding_pct', None)):
                if signal.signal == 'SHORT':
                    # Exit short if funding drops below P75
                    if bar['funding_pct'] < strategy.exit_high_pct:
                        # Calculate PnL at current close
                        pnl_pct = ((entry - bar['close']) / entry) * 100
                        if pnl_pct > 0:  # Only exit if profitable
                            hit_tp = True
                            exit_idx = j + 1
                            exit_reason = 'FUNDING_NORM'
                            break
                elif signal.signal == 'LONG':
                    # Exit long if funding rises above P25
                    if bar['funding_pct'] > strategy.exit_low_pct:
                        pnl_pct = ((bar['close'] - entry) / entry) * 100
                        if pnl_pct > 0:
                            hit_tp = True
                            exit_idx = j + 1
                            exit_reason = 'FUNDING_NORM'
                            break

        # If no exit, use last bar
        if not hit_tp and not hit_sl:
            exit_idx = len(future)
            exit_reason = 'TIMEOUT'
            # Calculate final PnL
            final_price = future.iloc[-1]['close']
            if signal.signal == 'LONG':
                pnl_pct = ((final_price - entry) / entry) * 100
            else:
                pnl_pct = ((entry - final_price) / entry) * 100

            # Consider timeout as win if profitable
            if pnl_pct > 0.5:  # > 0.5% profit
                hit_tp = True
            elif pnl_pct < -2.5:  # < -2.5% loss
                hit_sl = True

        outcome = 'WIN' if hit_tp else ('LOSS' if hit_sl else 'TIMEOUT')

        setup = {
            'timestamp': str(df.index[i]),
            'signal': signal.signal,
            'entry_price': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'outcome': outcome,
            'exit_reason': exit_reason,
            'hold_hours': exit_idx if exit_idx else strategy.max_hold_hours,
            'reasons': signal.reasons,
            'funding_rate': signal.funding_rate,
            'funding_pct': signal.funding_percentile,
        }

        setups.append(setup)

    print(f"\n✅ Found {len(setups)} setups")

    if len(setups) == 0:
        print("⚠️  No setups found - funding rates may not have reached extreme levels")
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

    # Average hold time
    avg_hold = sum(s['hold_hours'] for s in setups) / len(setups)
    print(f"   Avg Hold: {avg_hold:.1f} hours ({avg_hold/24:.1f} days)")

    # Exit reason breakdown
    exit_reasons = {}
    for s in setups:
        reason = s.get('exit_reason', 'UNKNOWN')
        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1

    print(f"\n📋 Exit Reasons:")
    for reason, count in exit_reasons.items():
        print(f"   {reason}: {count}")

    # Show examples
    print(f"\n📋 Sample Setups:")
    for setup in setups[:5]:
        print(f"   {setup['timestamp']} | {setup['signal']} | {setup['outcome']} | {setup['exit_reason']}")
        print(f"      Funding: {setup['funding_rate']*100:.4f}% (P{setup['funding_pct']:.0f})")
        print(f"      Hold: {setup['hold_hours']}h | {setup['reasons'][0]}")

    # Save for detailed analysis
    output = Path(__file__).parent.parent / 'data' / 'test_funding_setups.jsonl'
    with open(output, 'w') as f:
        for setup in setups:
            f.write(json.dumps(setup) + '\n')

    print(f"\n💾 Saved detailed results to: {output.name}")

    print(f"\n{'='*70}")

    # Verdict
    if losses > 0:
        if pf >= 1.3:
            print("✅ PROMISING - PF ≥ 1.3 - Worth full validation!")
        elif pf >= 1.1:
            print("⚠️  WEAK SIGNAL - PF 1.1-1.3 - Needs refinement")
        else:
            print("❌ NO EDGE - PF < 1.1 - Strategy fails")
    else:
        print("⚠️  Cannot calculate PF (no losses)")

    if wins + losses < 50:
        print("⚠️  WARNING: Sample size too small (< 50 trades)")

    print("="*70)


if __name__ == "__main__":
    test_strategy()
