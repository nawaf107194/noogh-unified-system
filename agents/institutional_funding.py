#!/usr/bin/env python3
"""
Institutional Funding Rate Validation
======================================
Proper validation of funding rate strategy with:
- De-duplication of overlapping trades
- 60/20/20 temporal split
- Permutation testing
- Bootstrap confidence intervals
- Cross-symbol validation
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading.funding_rate_strategy import get_funding_rate_strategy


def deduplicate_setups(setups: List[Dict], min_gap_hours: int = 24) -> List[Dict]:
    """
    Remove overlapping trades

    Strategy: Keep first signal in each funding extreme period.
    Skip subsequent signals within min_gap_hours of last kept signal.
    """
    if not setups:
        return []

    # Sort by timestamp
    setups_sorted = sorted(setups, key=lambda x: x['timestamp'])

    deduped = []
    last_kept_ts = None

    for setup in setups_sorted:
        ts = pd.Timestamp(setup['timestamp'])

        if last_kept_ts is None:
            # First setup
            deduped.append(setup)
            last_kept_ts = ts
        else:
            # Check gap
            hours_since_last = (ts - last_kept_ts).total_seconds() / 3600

            if hours_since_last >= min_gap_hours:
                deduped.append(setup)
                last_kept_ts = ts

    return deduped


def evaluate_setup(df: pd.DataFrame, idx: int, signal: dict, strategy) -> Dict:
    """
    Evaluate a single setup with proper backtesting

    Returns outcome dict with WIN/LOSS/TIMEOUT
    """
    entry = signal.entry_price
    sl = signal.stop_loss
    tp = signal.take_profit
    signal_type = signal.signal

    # Get future bars (up to max hold period)
    future = df.iloc[idx+1:idx+strategy.max_hold_hours+1]

    hit_tp = False
    hit_sl = False
    exit_idx = None
    exit_reason = None

    for j, (ts, bar) in enumerate(future.iterrows()):
        # Check TP/SL
        if signal_type == 'LONG':
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

        # Check funding normalization (but only if profitable)
        if not pd.isna(bar.get('funding_pct', None)):
            if signal_type == 'SHORT':
                if bar['funding_pct'] < strategy.exit_high_pct:
                    pnl_pct = ((entry - bar['close']) / entry) * 100
                    if pnl_pct > 0.2:  # Only exit if > 0.2% profit
                        hit_tp = True
                        exit_idx = j + 1
                        exit_reason = 'FUNDING_NORM'
                        break
            elif signal_type == 'LONG':
                if bar['funding_pct'] > strategy.exit_low_pct:
                    pnl_pct = ((bar['close'] - entry) / entry) * 100
                    if pnl_pct > 0.2:
                        hit_tp = True
                        exit_idx = j + 1
                        exit_reason = 'FUNDING_NORM'
                        break

    # Timeout handling
    if not hit_tp and not hit_sl:
        exit_idx = len(future)
        exit_reason = 'TIMEOUT'

        if len(future) > 0:
            final_price = future.iloc[-1]['close']
            if signal_type == 'LONG':
                pnl_pct = ((final_price - entry) / entry) * 100
            else:
                pnl_pct = ((entry - final_price) / entry) * 100

            # Classify timeout as win/loss based on PnL
            if pnl_pct > 0.5:
                hit_tp = True
            elif pnl_pct < -2.0:
                hit_sl = True

    outcome = 'WIN' if hit_tp else ('LOSS' if hit_sl else 'TIMEOUT')

    # Calculate R-multiple
    if signal_type == 'LONG':
        risk = entry - sl
        if exit_idx and len(future) > 0:
            exit_price = future.iloc[min(exit_idx-1, len(future)-1)]['close']
            pnl = exit_price - entry
        else:
            pnl = 0
    else:  # SHORT
        risk = sl - entry
        if exit_idx and len(future) > 0:
            exit_price = future.iloc[min(exit_idx-1, len(future)-1)]['close']
            pnl = entry - exit_price
        else:
            pnl = 0

    r_multiple = pnl / risk if risk > 0 else 0

    return {
        'outcome': outcome,
        'exit_reason': exit_reason,
        'hold_hours': exit_idx if exit_idx else strategy.max_hold_hours,
        'r_multiple': r_multiple
    }


def calculate_metrics(r_multiples: np.ndarray) -> Dict:
    """Calculate performance metrics from R-multiples"""
    if len(r_multiples) == 0:
        return {
            'n_trades': 0,
            'win_rate': 0,
            'pf': 0,
            'avg_r': 0,
            'sharpe': 0,
            'max_dd': 0
        }

    wins = r_multiples[r_multiples > 0]
    losses = r_multiples[r_multiples < 0]

    win_rate = len(wins) / len(r_multiples) if len(r_multiples) > 0 else 0

    win_r = wins.sum() if len(wins) > 0 else 0
    loss_r = abs(losses.sum()) if len(losses) > 0 else 0

    if loss_r > 0:
        pf = win_r / loss_r
    elif win_r > 0:
        pf = float('inf')
    else:
        pf = 0

    avg_r = r_multiples.mean()
    sharpe = r_multiples.mean() / r_multiples.std() if r_multiples.std() > 0 else 0

    # Max drawdown
    cumulative = np.cumsum(r_multiples)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = running_max - cumulative
    max_dd = drawdown.max() if len(drawdown) > 0 else 0

    return {
        'n_trades': len(r_multiples),
        'win_rate': win_rate,
        'pf': pf if not np.isinf(pf) else 100.0,
        'avg_r': avg_r,
        'sharpe': sharpe,
        'max_dd': max_dd
    }


def permutation_test_pf(r_multiples: np.ndarray, n: int = 500) -> float:
    """
    Monte Carlo permutation test

    H0: R-multiples are random (no predictive power)
    Returns: p-value
    """
    if len(r_multiples) < 10:
        return 1.0

    # Observed metric
    observed = calculate_metrics(r_multiples)['pf']
    if np.isinf(observed):
        observed = 100.0

    # Permutation distribution
    perm_pfs = []
    for _ in range(n):
        # Random shuffle (breaks temporal order)
        shuffled = np.random.permutation(r_multiples)
        perm_pf = calculate_metrics(shuffled)['pf']
        perm_pfs.append(perm_pf)

    perm_pfs = np.array(perm_pfs)

    # p-value: proportion of permutations >= observed
    p_value = (perm_pfs >= observed).sum() / n

    return p_value


def bootstrap_ci(r_multiples: np.ndarray, n: int = 1000, alpha: float = 0.05) -> Tuple[float, float]:
    """Bootstrap confidence interval for average R"""
    if len(r_multiples) < 10:
        return (0, 0)

    bootstrap_means = []
    for _ in range(n):
        sample = np.random.choice(r_multiples, size=len(r_multiples), replace=True)
        bootstrap_means.append(sample.mean())

    bootstrap_means = np.array(bootstrap_means)
    lower = np.percentile(bootstrap_means, alpha/2 * 100)
    upper = np.percentile(bootstrap_means, (1 - alpha/2) * 100)

    return (lower, upper)


def generate_and_evaluate_setups(df: pd.DataFrame, strategy, start_idx: int, end_idx: int) -> List[Dict]:
    """
    Generate setups in a date range and evaluate them

    Returns list of evaluated setups with outcomes
    """
    setups = []

    for i in range(start_idx, end_idx):
        signal = strategy.generate_signal(df, i)

        if signal.signal == 'NONE':
            continue

        # Evaluate outcome
        outcome = evaluate_setup(df, i, signal, strategy)

        setup = {
            'timestamp': str(df.index[i]),
            'signal': signal.signal,
            'entry_price': signal.entry_price,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'funding_rate': signal.funding_rate,
            'funding_pct': signal.funding_percentile,
            'outcome': outcome['outcome'],
            'exit_reason': outcome['exit_reason'],
            'hold_hours': outcome['hold_hours'],
            'r_multiple': outcome['r_multiple']
        }

        setups.append(setup)

    return setups


def validate_funding_strategy(symbol: str = "BTCUSDT") -> Dict:
    """
    Full institutional validation pipeline
    """
    print("="*70)
    print(f"🏛️  INSTITUTIONAL VALIDATION: {symbol}")
    print("="*70)

    # Load data
    data_file = Path(__file__).parent.parent / 'data' / f'{symbol}_1h_with_funding_12M.parquet'

    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return {}

    df = pd.read_parquet(data_file)
    print(f"\n✅ Loaded {len(df):,} 1h candles")
    print(f"   Date range: {df.index[0]} → {df.index[-1]}")

    # Initialize strategy
    strategy = get_funding_rate_strategy()

    # Compute indicators
    print(f"\n🔧 Computing indicators...")
    df = strategy.compute_indicators(df)

    # Define splits (60/20/20)
    n = len(df)
    lookback = strategy.lookback_days * 3 + 100

    train_end = lookback + int((n - lookback) * 0.6)
    val_end = train_end + int((n - lookback) * 0.2)

    print(f"\n📊 Temporal Split (60/20/20):")
    print(f"   Train: {df.index[lookback]} → {df.index[train_end-1]} ({train_end - lookback} bars)")
    print(f"   Val:   {df.index[train_end]} → {df.index[val_end-1]} ({val_end - train_end} bars)")
    print(f"   OOS:   {df.index[val_end]} → {df.index[-strategy.max_hold_hours-1]} ({n - val_end - strategy.max_hold_hours} bars)")

    # Generate setups for each period
    print(f"\n🔍 Generating setups...")

    train_setups = generate_and_evaluate_setups(df, strategy, lookback, train_end)
    val_setups = generate_and_evaluate_setups(df, strategy, train_end, val_end)
    oos_setups = generate_and_evaluate_setups(df, strategy, val_end, n - strategy.max_hold_hours)

    print(f"   Raw Train: {len(train_setups)} setups")
    print(f"   Raw Val:   {len(val_setups)} setups")
    print(f"   Raw OOS:   {len(oos_setups)} setups")

    # De-duplicate (24h minimum gap)
    print(f"\n🧹 De-duplicating overlapping trades (24h min gap)...")

    train_deduped = deduplicate_setups(train_setups, min_gap_hours=24)
    val_deduped = deduplicate_setups(val_setups, min_gap_hours=24)
    oos_deduped = deduplicate_setups(oos_setups, min_gap_hours=24)

    print(f"   Train: {len(train_setups)} → {len(train_deduped)} (-{len(train_setups) - len(train_deduped)} overlaps)")
    print(f"   Val:   {len(val_setups)} → {len(val_deduped)} (-{len(val_setups) - len(val_deduped)} overlaps)")
    print(f"   OOS:   {len(oos_setups)} → {len(oos_deduped)} (-{len(oos_setups) - len(oos_deduped)} overlaps)")

    # Calculate metrics
    train_r = np.array([s['r_multiple'] for s in train_deduped])
    val_r = np.array([s['r_multiple'] for s in val_deduped])
    oos_r = np.array([s['r_multiple'] for s in oos_deduped])

    train_metrics = calculate_metrics(train_r)
    val_metrics = calculate_metrics(val_r)
    oos_metrics = calculate_metrics(oos_r)

    print(f"\n{'='*70}")
    print(f"📊 RESULTS (De-duplicated)")
    print(f"{'='*70}")

    print(f"\n🟢 TRAIN:")
    print(f"   Trades: {train_metrics['n_trades']}")
    print(f"   Win Rate: {train_metrics['win_rate']*100:.1f}%")
    print(f"   PF: {train_metrics['pf']:.2f}")
    print(f"   Avg R: {train_metrics['avg_r']:.3f}")
    print(f"   Sharpe: {train_metrics['sharpe']:.2f}")

    print(f"\n🟡 VALIDATION:")
    print(f"   Trades: {val_metrics['n_trades']}")
    print(f"   Win Rate: {val_metrics['win_rate']*100:.1f}%")
    print(f"   PF: {val_metrics['pf']:.2f}")
    print(f"   Avg R: {val_metrics['avg_r']:.3f}")
    print(f"   Sharpe: {val_metrics['sharpe']:.2f}")

    print(f"\n🔴 OUT-OF-SAMPLE:")
    print(f"   Trades: {oos_metrics['n_trades']}")
    print(f"   Win Rate: {oos_metrics['win_rate']*100:.1f}%")
    print(f"   PF: {oos_metrics['pf']:.2f}")
    print(f"   Avg R: {oos_metrics['avg_r']:.3f}")
    print(f"   Sharpe: {oos_metrics['sharpe']:.2f}")

    # Permutation test on OOS
    if len(oos_r) >= 10:
        print(f"\n🎲 Monte Carlo Permutation Test (OOS, n=500)...")
        p_value = permutation_test_pf(oos_r, n=500)
        print(f"   p-value: {p_value:.4f}")

        if p_value <= 0.01:
            print(f"   ✅ HIGHLY SIGNIFICANT (p ≤ 0.01)")
        elif p_value <= 0.05:
            print(f"   ✅ SIGNIFICANT (p ≤ 0.05)")
        elif p_value <= 0.10:
            print(f"   ⚠️  MARGINAL (p ≤ 0.10)")
        else:
            print(f"   ❌ NOT SIGNIFICANT (p > 0.10)")
    else:
        p_value = 1.0
        print(f"\n⚠️  Sample too small for permutation test")

    # Bootstrap CI
    if len(oos_r) >= 10:
        print(f"\n📊 Bootstrap Confidence Interval (OOS, n=1000)...")
        ci_lower, ci_upper = bootstrap_ci(oos_r, n=1000)
        print(f"   95% CI for Avg R: [{ci_lower:.3f}, {ci_upper:.3f}]")

    print(f"\n{'='*70}")
    print(f"🎯 SUCCESS CRITERIA CHECK:")
    print(f"{'='*70}")

    criteria_met = 0
    total_criteria = 4

    # 1. OOS PF ≥ 1.2
    if oos_metrics['pf'] >= 1.2:
        print(f"✅ OOS PF ≥ 1.2: {oos_metrics['pf']:.2f}")
        criteria_met += 1
    else:
        print(f"❌ OOS PF < 1.2: {oos_metrics['pf']:.2f}")

    # 2. p-value ≤ 0.05
    if p_value <= 0.05:
        print(f"✅ p-value ≤ 0.05: {p_value:.4f}")
        criteria_met += 1
    else:
        print(f"❌ p-value > 0.05: {p_value:.4f}")

    # 3. OOS trades ≥ 50
    if oos_metrics['n_trades'] >= 50:
        print(f"✅ OOS trades ≥ 50: {oos_metrics['n_trades']}")
        criteria_met += 1
    else:
        print(f"❌ OOS trades < 50: {oos_metrics['n_trades']}")

    print(f"\n⏳ Cross-symbol validation pending (need ≥ 2 symbols)")

    print(f"\n{'='*70}")

    if criteria_met >= 3:
        print(f"✅ PASSED {criteria_met}/4 criteria (pending multi-symbol)")
    else:
        print(f"❌ FAILED - Only {criteria_met}/4 criteria met")

    print(f"{'='*70}")

    return {
        'symbol': symbol,
        'train': train_metrics,
        'val': val_metrics,
        'oos': oos_metrics,
        'p_value': p_value,
        'criteria_met': criteria_met,
        'oos_setups': oos_deduped
    }


if __name__ == "__main__":
    result = validate_funding_strategy("BTCUSDT")
