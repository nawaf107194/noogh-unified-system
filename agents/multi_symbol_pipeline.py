#!/usr/bin/env python3
"""
Multi-Symbol Validation Pipeline
=================================
Generates setups and runs PSO for BTC, ETH, BNB, SOL
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading.trap_hybrid_engine import get_trap_hybrid_engine
from trading.regimes import compute_regime_tags, compute_features

# Import PSO components from no_layer_b script
exec(open(Path(__file__).parent / "institutional_pso_no_layer_b.py").read(), globals())


def generate_setups_for_symbol(symbol: str) -> List[Dict]:
    """Generate setups for a symbol"""
    print(f"\n{'='*70}")
    print(f"🔍 GENERATING SETUPS - {symbol}")
    print(f"{'='*70}")

    data_dir = Path(__file__).parent.parent / 'data'

    # Load data
    df_5m = pd.read_parquet(data_dir / f"{symbol}_5m_12M.parquet")
    df_1h = pd.read_parquet(data_dir / f"{symbol}_1h_12M.parquet")

    print(f"✅ Loaded: {len(df_5m):,} 5m candles, {len(df_1h):,} 1h candles")

    # Compute indicators
    trap_engine = get_trap_hybrid_engine()
    df_5m = trap_engine.compute_indicators(df_5m)

    setups = []
    last_log = 0

    # Scan for setups
    for i in range(100, len(df_5m) - 50):
        if i - last_log >= 20000:
            print(f"   Progress: {(i / len(df_5m)) * 100:.1f}%")
            last_log = i

        signal = trap_engine.generate_signal(df_5m, current_idx=i)
        if signal.signal == 'NONE':
            continue

        # Calculate outcome
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
                if h >= take_profit:
                    hit_tp = True
                    break
                if l <= stop_loss:
                    hit_sl = True
                    break
                max_profit = max(max_profit, ((h - entry_price) / entry_price) * 100)
                max_loss = min(max_loss, ((l - entry_price) / entry_price) * 100)
            else:  # SHORT
                if l <= take_profit:
                    hit_tp = True
                    break
                if h >= stop_loss:
                    hit_sl = True
                    break
                max_profit = max(max_profit, ((entry_price - l) / entry_price) * 100)
                max_loss = min(max_loss, ((entry_price - h) / entry_price) * 100)

        outcome = 'WIN' if hit_tp else ('LOSS' if hit_sl else 'TIMEOUT')

        # Get context
        timestamp = df_5m.index[i]
        micro_slice = df_5m.iloc[max(0, i-100):i+1]
        macro_slice = df_1h[df_1h.index <= timestamp].iloc[-100:]

        regime_tags = compute_regime_tags(micro_slice, macro_slice)
        features = compute_features(micro_slice, macro_slice)

        bar = df_5m.iloc[i]

        setup = {
            'timestamp': str(timestamp),
            'symbol': symbol,
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
            'rsi': float(bar.get('rsi', 50)),
            'volume': float(bar.get('volume', 0)),
            'taker_buy_ratio': float(bar.get('taker_buy_base', 0) / bar.get('volume', 1)) if bar.get('volume', 0) > 0 else 0.5,
            **regime_tags,
            **features,
        }

        setups.append(setup)

    print(f"✅ Generated {len(setups)} setups")

    # Quick stats
    wins = sum(1 for s in setups if s['outcome'] == 'WIN')
    losses = sum(1 for s in setups if s['outcome'] == 'LOSS')
    raw_pf = wins / losses if losses > 0 else 0

    print(f"   Wins: {wins}, Losses: {losses}")
    print(f"   Raw PF: {raw_pf:.2f}")

    # Save
    output_file = data_dir / f"backtest_setups_{symbol}.jsonl"
    with open(output_file, 'w') as f:
        for setup in setups:
            f.write(json.dumps(setup) + '\n')

    print(f"💾 Saved: {output_file.name}")

    return setups


def run_pso_for_symbol(symbol: str, setups: List[Dict]) -> Dict:
    """Run PSO optimization for a symbol"""
    print(f"\n{'='*70}")
    print(f"🧬 PSO OPTIMIZATION - {symbol}")
    print(f"{'='*70}")

    # Temporal sort
    setups.sort(key=lambda x: x.get("timestamp", ""))

    n = len(setups)
    i1 = int(n * 0.60)
    i2 = int(n * 0.80)

    train = setups[:i1]
    val = setups[i1:i2]
    oos = setups[i2:]

    print(f"Total={n} | Train={len(train)} | Val={len(val)} | OOS={len(oos)}")

    if n < 200:
        print("⚠️  Not enough setups")
        return None

    # Run PSO
    ev = Evaluator(setups)
    pso = PSO(ev, train, val, n_particles=40, max_iter=60)

    best_policy, best_fit = pso.optimize()

    # Evaluate
    r_train = ev.evaluate(best_policy, train, "TRAIN")
    r_val = ev.evaluate(best_policy, val, "VAL")
    r_oos = ev.evaluate(best_policy, oos, "OOS")

    # Collect OOS R values for permutation test
    oos_r = []
    for s in oos:
        x = extract_features(s)
        passed, _ = best_policy(x)
        if not passed:
            continue
        r = ev.r_multiple(s)
        if r is not None:
            oos_r.append(float(r))

    p_value = permutation_test_pf(oos_r, n=500)

    print(f"\n📊 RESULTS - {symbol}:")
    print(f"   Train: {r_train['n_trades']} trades, PF {r_train['pf']:.2f}, DD {r_train['max_dd']:.1f}%")
    print(f"   Val:   {r_val['n_trades']} trades, PF {r_val['pf']:.2f}, DD {r_val['max_dd']:.1f}%")
    print(f"   OOS:   {r_oos['n_trades']} trades, PF {r_oos['pf']:.2f}, DD {r_oos['max_dd']:.1f}%")
    print(f"   P-value: {p_value:.4f}")

    return {
        'symbol': symbol,
        'raw_pf': wins / losses if 'wins' in locals() and 'losses' in locals() and losses > 0 else 0,
        'train': r_train,
        'val': r_val,
        'oos': r_oos,
        'p_value': p_value,
        'policy': best_policy.to_dict(),
    }


def main():
    """Run multi-symbol validation"""
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]

    print("="*70)
    print("🏛️ MULTI-SYMBOL VALIDATION PIPELINE")
    print("="*70)

    results = {}

    for symbol in symbols:
        # Generate setups
        setups = generate_setups_for_symbol(symbol)

        if len(setups) < 200:
            print(f"⚠️  {symbol}: Not enough setups, skipping")
            continue

        # Run PSO
        result = run_pso_for_symbol(symbol, setups)

        if result:
            results[symbol] = result

    # Print final comparison table
    print(f"\n{'='*70}")
    print("📊 MULTI-SYMBOL COMPARISON")
    print(f"{'='*70}")
    print(f"\n{'Symbol':<10} | {'OOS Trades':>10} | {'Raw PF':>8} | {'PSO PF (OOS)':>14} | {'P-value':>9} | {'Verdict':<20}")
    print(f"{'-'*10}-+-{'-'*10}-+-{'-'*8}-+-{'-'*14}-+-{'-'*9}-+-{'-'*20}")

    for symbol, res in results.items():
        oos_trades = res['oos']['n_trades']
        # Calculate raw PF from setups
        data_file = Path(f"/home/noogh/projects/noogh_unified_system/src/data/backtest_setups_{symbol}.jsonl")
        with open(data_file) as f:
            setups = [json.loads(line) for line in f]
        wins = sum(1 for s in setups if s['outcome'] == 'WIN')
        losses = sum(1 for s in setups if s['outcome'] == 'LOSS')
        raw_pf = wins / losses if losses > 0 else 0

        pso_pf = res['oos']['pf']
        p_val = res['p_value']

        # Verdict
        if pso_pf >= 1.3 and p_val <= 0.05:
            verdict = "✅ STRONG ALPHA"
        elif pso_pf >= 1.2 and p_val <= 0.10:
            verdict = "⚠️  WEAK ALPHA"
        else:
            verdict = "❌ NO ALPHA"

        print(f"{symbol:<10} | {oos_trades:>10} | {raw_pf:>8.2f} | {pso_pf:>14.2f} | {p_val:>9.4f} | {verdict:<20}")

    print(f"\n{'='*70}")
    print("✅ MULTI-SYMBOL VALIDATION COMPLETE")
    print("="*70)

    # Save results
    results_file = Path("/home/noogh/projects/noogh_unified_system/src/data/multi_symbol_results.json")
    with open(results_file, 'w') as f:
        # Convert to serializable format
        serializable = {}
        for sym, res in results.items():
            serializable[sym] = {
                'oos_trades': res['oos']['n_trades'],
                'oos_pf': res['oos']['pf'],
                'oos_dd': res['oos']['max_dd'],
                'p_value': res['p_value'],
                'train_pf': res['train']['pf'],
                'val_pf': res['val']['pf'],
            }
        json.dump(serializable, f, indent=2)

    print(f"\n💾 Results saved to: {results_file}")


if __name__ == "__main__":
    np.random.seed(42)
    main()
