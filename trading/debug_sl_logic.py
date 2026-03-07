"""
Debug script to understand the SL calculation issue
"""
import os
import pandas as pd
import numpy as np
from trading.technical_indicators import (
    TechnicalIndicatorsV2, SignalEngineV3_LiquidityTrap,
    IndicatorConfig, RiskConfig
)

symbol = "BTCUSDT"
data_dir = os.path.join(os.path.dirname(__file__), "data")
micro_path = os.path.join(data_dir, f"{symbol}_5m_3M.parquet")
macro_path = os.path.join(data_dir, f"{symbol}_1h_3M.parquet")

df_micro = pd.read_parquet(micro_path)
df_macro = pd.read_parquet(macro_path)

# Find a signal and debug it
cfg = IndicatorConfig()
risk_cfg = RiskConfig(min_rrr=1.5)

print("Searching for signals in first 1000 bars...")
for i in range(500, 1000):
    micro_slice = df_micro.iloc[:i+1]
    macro_slice = df_macro.loc[:micro_slice.index[-1]]

    sig = SignalEngineV3_LiquidityTrap.generate_entry_signal(
        df_macro=macro_slice,
        df_micro=micro_slice,
        cfg=cfg,
        risk_cfg=risk_cfg
    )

    if sig['signal'] in ('LONG', 'SHORT'):
        print(f"\n{'='*80}")
        print(f"Found {sig['signal']} signal at index {i} / {micro_slice.index[-1]}")
        print(f"{'='*80}")

        # Get the relevant data
        entry_price = sig['entry_price']
        stop_loss = sig['stop_loss']
        atr_val = sig['atr']

        print(f"\n📍 Entry Price: {entry_price:.2f}")
        print(f"🛑 Stop Loss: {stop_loss:.2f}")
        print(f"📏 ATR: {atr_val:.2f}")
        print(f"📊 Distance: {abs(entry_price - stop_loss):.2f}")
        print(f"💹 Risk (R): {abs(entry_price - stop_loss) / entry_price * 100:.3f}%")

        # Check last bars
        print(f"\n📈 Last 3 bars:")
        recent = df_micro.iloc[i-2:i+1][['open', 'high', 'low', 'close']]
        for idx, row in recent.iterrows():
            print(f"   {idx}: O={row['open']:.2f}, H={row['high']:.2f}, L={row['low']:.2f}, C={row['close']:.2f}")

        # Debug the SL calculation
        sweep_idx = i - 1  # bar[-2] relative to signal bar
        if sig['signal'] == 'LONG':
            sweep_low = df_micro.iloc[sweep_idx]['low']
            atr_based_sl = entry_price - atr_val * risk_cfg.base_sl_atr_mult
            sweep_based_sl = sweep_low - atr_val * 0.3

            print(f"\n🔍 LONG SL Calculation:")
            print(f"   Sweep Low (bar[-2]): {sweep_low:.2f}")
            print(f"   ATR-based SL: {atr_based_sl:.2f}")
            print(f"   Sweep-based SL: {sweep_based_sl:.2f}")
            print(f"   Sweep < Entry? {sweep_based_sl < entry_price}")

            if sweep_based_sl < entry_price:
                chosen_sl = max(atr_based_sl, sweep_based_sl)
                print(f"   ✓ Using max() = {chosen_sl:.2f}")
            else:
                chosen_sl = atr_based_sl
                print(f"   ✓ Sweep too high, using ATR-based = {chosen_sl:.2f}")

            print(f"   Final SL from signal: {stop_loss:.2f}")
            print(f"   Match? {abs(chosen_sl - stop_loss) < 0.01}")

        else:  # SHORT
            sweep_high = df_micro.iloc[sweep_idx]['high']
            atr_based_sl = entry_price + atr_val * risk_cfg.base_sl_atr_mult
            sweep_based_sl = sweep_high + atr_val * 0.3

            print(f"\n🔍 SHORT SL Calculation:")
            print(f"   Sweep High (bar[-2]): {sweep_high:.2f}")
            print(f"   ATR-based SL: {atr_based_sl:.2f}")
            print(f"   Sweep-based SL: {sweep_based_sl:.2f}")
            print(f"   Sweep > Entry? {sweep_based_sl > entry_price}")

            if sweep_based_sl > entry_price:
                chosen_sl = min(atr_based_sl, sweep_based_sl)
                print(f"   ✓ Using min() = {chosen_sl:.2f}")
            else:
                chosen_sl = atr_based_sl
                print(f"   ✓ Sweep too low, using ATR-based = {chosen_sl:.2f}")

            print(f"   Final SL from signal: {stop_loss:.2f}")
            print(f"   Match? {abs(chosen_sl - stop_loss) < 0.01}")

        # Show reasons
        print(f"\n📋 Reasons: {sig.get('reasons', [])}")

        # Only show first 3 signals
        input("\nPress Enter to see next signal (or Ctrl+C to quit)...")
