import pandas as pd
import json
from pathlib import Path
from trading.regimes import compute_regime_tags, compute_features, _ema, _atr

# Read existing setups
setups_path = Path("data/backtest_setups.jsonl")
output_path = Path("data/backtest_setups_regimes.jsonl")

# Load parquet data
df_micro = pd.read_parquet("trading/data/BTCUSDT_5m_3M.parquet")
df_macro = pd.read_parquet("trading/data/BTCUSDT_1h_3M.parquet")

count = 0
with open(setups_path, "r") as f_in, open(output_path, "w") as f_out:
    for line in f_in:
        if not line.strip(): continue
        setup = json.loads(line)
        ts = setup.get("timestamp")
        if not ts: continue
        
        # Get data directly before the timestamp
        ts_dt = pd.to_datetime(ts)
        # Using less than since we want data right before the trade
        micro_slice = df_micro.loc[:ts_dt - pd.Timedelta(seconds=1)]
        macro_slice = df_macro.loc[:ts_dt - pd.Timedelta(seconds=1)]
        
        # Get enough history for 50 bars
        if len(micro_slice) > 0 and len(macro_slice) > 0:
            micro_slice = micro_slice.iloc[-150:]
            macro_slice = macro_slice.iloc[-150:]
            
            # Since _atr, _adx etc take pd.DataFrame, and assume high low close,
            # wait, the regime functions use _ema, _rsi, _atr.
            try:
                tags = compute_regime_tags(micro_slice, macro_slice)
                feats = compute_features(micro_slice, macro_slice)
                
                # Merge into setup
                setup.update(tags)
                setup.update(feats)
            except Exception as e:
                print(f"Error computing regimes for {ts}: {e}")
        
        f_out.write(json.dumps(setup) + "\\n")
        count += 1
        
print(f"Exported {count} setups with regime tags to {output_path}")
