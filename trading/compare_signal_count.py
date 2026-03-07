"""
Compare signal count between vectorized and backtesting_v2
اكتشاف لماذا عدد الصفقات مختلف
"""
import os
import numpy as np
import pandas as pd
from trading.trap_vectorized_backtest import compute_signals

# Load data
symbol = "BTCUSDT"
data_dir = os.path.join(os.path.dirname(__file__), "data")
micro_path = os.path.join(data_dir, f"{symbol}_5m_3M.parquet")

print("Loading data...")
df = pd.read_parquet(micro_path)
print(f"Loaded {len(df)} bars")

# Compute signals (vectorized approach)
print("\nComputing signals...")
df = compute_signals(df)

long_signals = df["long_signal"].sum()
short_signals = df["short_signal"].sum()
total_signals = long_signals + short_signals

print(f"\n📊 Vectorized Signal Count:")
print(f"   LONG signals: {long_signals}")
print(f"   SHORT signals: {short_signals}")
print(f"   TOTAL signals: {total_signals}")

# Show sample signals
print(f"\n📋 Sample LONG signals (first 5):")
long_sig_df = df[df["long_signal"] == True].head()
if len(long_sig_df) > 0:
    print(long_sig_df[['close', 'atr', 'delta', 'bull_sweep']].to_string())

print(f"\n📋 Sample SHORT signals (first 5):")
short_sig_df = df[df["short_signal"] == True].head()
if len(short_sig_df) > 0:
    print(short_sig_df[['close', 'atr', 'delta', 'bear_sweep']].to_string())

print(f"\n💡 Expected trades in backtest: ~{total_signals}")
print(f"   Actual trades (RRR=1.0): 129")
print(f"   Missing: {total_signals - 129}")
print(f"\n   Possible reasons:")
print(f"   1. TP1 calculation fails (RRR validation)")
print(f"   2. Entry shift causes invalid SL")
print(f"   3. Quantity calculation returns 0")
print(f"   4. Different signal generation logic in SignalEngineV3")
