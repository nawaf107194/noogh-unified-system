"""
Debug Missing Trades: اكتشاف لماذا 119 صفقة مفقودة
نتتبع كل signal rejection
"""
import os
import pandas as pd
import numpy as np
import logging
from trading.backtesting_v2 import prepare_aligned_data, position_size_from_risk, BacktestConfig
from trading.technical_indicators import (
    IndicatorConfig, ScoreWeights, RiskConfig,
    SignalEngineV3_LiquidityTrap
)

logging.basicConfig(level=logging.WARNING)  # Suppress info logs

def debug_signal_rejections():
    """تتبع كل signal وسبب rejection"""

    symbol = "BTCUSDT"
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    micro_path = os.path.join(data_dir, f"{symbol}_5m_3M.parquet")
    macro_path = os.path.join(data_dir, f"{symbol}_1h_3M.parquet")

    df_micro = pd.read_parquet(micro_path)
    df_macro = pd.read_parquet(macro_path)

    bt = BacktestConfig(
        initial_capital=10_000.0,
        risk_per_trade=0.01,
        commission_rate=0.0004,
        slippage_rate=0.0002
    )

    risk_cfg = RiskConfig(min_rrr=1.0, tp2_mult=float('nan'), tp3_mult=float('nan'))

    aligned = prepare_aligned_data(df_micro, df_macro)

    _need = ["open", "high", "low", "close", "volume"]
    if "taker_buy_base" in df_micro.columns:
        _need.append("taker_buy_base")

    equity = bt.initial_capital
    idxs = aligned.index

    # Track rejections
    rejections = {
        'no_signal': 0,
        'no_stop_loss': 0,
        'invalid_sl': 0,
        'no_tp1': 0,
        'qty_zero': 0,
        'accepted': 0
    }

    rejection_details = []

    state = None  # Track if in position

    for i in range(len(aligned) - 2):
        ts = idxs[i]
        row = aligned.iloc[i]
        next_row = aligned.iloc[i + 1]

        # Skip if in position
        if state is not None:
            # Simple: just check if we'd still be in position
            # For debug purposes, assume position exits after 10 bars
            if i - state['entry_idx'] > 10:
                state = None
            continue

        # If flat, evaluate signal
        if state is None:
            micro_slice = aligned.iloc[: i + 1][_need].copy()
            macro_slice = df_macro.loc[:ts].copy()

            sig = SignalEngineV3_LiquidityTrap.generate_entry_signal(
                df_macro=macro_slice,
                df_micro=micro_slice,
                cfg=IndicatorConfig(),
                w=ScoreWeights(),
                risk_cfg=risk_cfg,
            )

            signal = sig.get("signal")

            if signal not in ("LONG", "SHORT"):
                rejections['no_signal'] += 1
                continue

            # Check stop loss
            if sig.get("stop_loss") is None:
                rejections['no_stop_loss'] += 1
                rejection_details.append({
                    'time': ts,
                    'signal': signal,
                    'reason': 'no_stop_loss',
                    'entry': sig.get('entry_price'),
                    'sl': None
                })
                continue

            # Entry price
            raw_entry = float(next_row["open"])
            exec_entry = raw_entry  # Simplified for debug

            sig_entry = float(sig.get("entry_price", row["close"]))
            entry_shift = exec_entry - sig_entry

            sl = float(sig["stop_loss"]) + entry_shift
            tps = sig.get("take_profits") or {}
            _tp1 = float(tps.get("tp1", np.nan)) + entry_shift if np.isfinite(tps.get("tp1", np.nan)) else np.nan

            # Validate SL
            MIN_RISK_PCT = 0.0001
            risk = abs(exec_entry - sl)
            is_valid_sl = (
                np.isfinite(sl) and
                risk > exec_entry * MIN_RISK_PCT and
                ((signal == "LONG" and sl < exec_entry) or (signal == "SHORT" and sl > exec_entry))
            )

            if not is_valid_sl:
                rejections['invalid_sl'] += 1
                rejection_details.append({
                    'time': ts,
                    'signal': signal,
                    'reason': 'invalid_sl',
                    'entry': exec_entry,
                    'sl': sl,
                    'risk_pct': risk / exec_entry * 100
                })
                continue

            # Check TP1
            if not np.isfinite(_tp1):
                rejections['no_tp1'] += 1
                rejection_details.append({
                    'time': ts,
                    'signal': signal,
                    'reason': 'no_tp1',
                    'entry': exec_entry,
                    'sl': sl,
                    'tp1': _tp1
                })
                continue

            # Size from risk
            qty = position_size_from_risk(
                capital=equity,
                entry=exec_entry,
                stop=sl,
                risk_per_trade=bt.risk_per_trade,
                max_leverage=bt.max_leverage,
            )

            if qty <= 0:
                rejections['qty_zero'] += 1
                rejection_details.append({
                    'time': ts,
                    'signal': signal,
                    'reason': 'qty_zero',
                    'entry': exec_entry,
                    'sl': sl,
                    'qty': qty
                })
                continue

            # Accepted!
            rejections['accepted'] += 1
            state = {'entry_idx': i + 1, 'qty': qty}

    # Print results
    print("\n" + "="*80)
    print("          🔍 MISSING TRADES DEBUG REPORT")
    print("="*80)

    print(f"\n📊 Signal Rejection Breakdown:")
    print(f"   Total bars analyzed: {len(aligned) - 2}")
    print(f"   No signal (NEUTRAL): {rejections['no_signal']}")
    print(f"   No stop loss: {rejections['no_stop_loss']}")
    print(f"   Invalid SL: {rejections['invalid_sl']}")
    print(f"   No TP1: {rejections['no_tp1']}")
    print(f"   Quantity = 0: {rejections['qty_zero']}")
    print(f"   ✅ Accepted: {rejections['accepted']}")

    total_rejections = sum(v for k, v in rejections.items() if k != 'accepted')
    print(f"\n   Total rejections: {total_rejections}")
    print(f"   Acceptance rate: {rejections['accepted'] / (rejections['accepted'] + total_rejections) * 100:.1f}%")

    # Show sample rejections
    if len(rejection_details) > 0:
        print(f"\n📋 Sample Rejections (first 10):")
        details_df = pd.DataFrame(rejection_details).head(10)
        print(details_df.to_string(index=False))

    # Compare with vectorized
    print(f"\n\n💡 COMPARISON:")
    print(f"   Vectorized signals: 248")
    print(f"   backtesting_v2 accepted: {rejections['accepted']}")
    print(f"   Difference: {248 - rejections['accepted']}")

    if rejections['no_tp1'] > 0:
        print(f"\n   ⚠️ MAJOR ISSUE: {rejections['no_tp1']} signals rejected due to no_tp1")
        print(f"      This suggests RRR calculation is failing!")

    if rejections['invalid_sl'] > 0:
        print(f"\n   ⚠️ ISSUE: {rejections['invalid_sl']} signals rejected due to invalid_sl")
        print(f"      Entry shift may be causing SL to flip sides")

    print("\n" + "="*80)
    print()


if __name__ == "__main__":
    debug_signal_rejections()
