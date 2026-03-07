import asyncio
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

from trading.binance_futures import BinanceFuturesManager
from trading.technical_indicators import IndicatorConfig, ScoreWeights, RiskConfig
from trading.backtesting_v2 import backtest_v2, BacktestConfig, grid_search_optimizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_optimization():
    print("🚀 Starting Historical Data Fetch & Optimization Pipeline (Level B OrderFlow)")
    
    # Initialize connection
    binance = BinanceFuturesManager(testnet=False, read_only=True)
    symbol = "BTCUSDT"
    
    print(f"📥 Fetching data for {symbol}...")
    
    # For training/optimization, we want a decent amount of data. e.g. 1500 bars.
    # We fetch 1h for macro and 5m for micro
    df_macro = binance.get_klines(symbol, '1h', limit=1500)
    df_micro = binance.get_klines(symbol, '5m', limit=1500)
    
    if df_macro is None or df_micro is None:
        print("❌ Failed to fetch data.")
        return
        
    print(f"✅ Data fetched. Macro: {len(df_macro)} bars, Micro: {len(df_micro)} bars.")
    
    # ----------------------------------------------------
    # GRID SEARCH OPTIMIZATION
    # ----------------------------------------------------
    print(br"=========================================")
    print(br"       GRID SEARCH OPTIMIZATION          ")
    print(br"=========================================")
    
    grid = {
        "min_score": [50, 60, 70],
        "atr_mult": [1.5, 2.0, 2.5],
        "fvg_gap": [0.1, 0.25, 0.5]
    }
    
    print(f"🔎 Testing Grid: {grid}")
    
    best_params, top_results = grid_search_optimizer(df_micro, df_macro, grid)
    
    print(f"\n🏆 Best Parameters Found:")
    print(best_params)
    
    print("\n📊 Top 5 Results (Score, min_score, atr_mult, fvg_gap):")
    for res in top_results[:5]:
        print(f"  {res}")
        
    # ----------------------------------------------------
    # RUN FINAL FULL BACKTEST WITH BEST PARAMS
    # ----------------------------------------------------
    print(br"\n=========================================")
    print(br"   FINAL FULL BACKTEST (Best Params)     ")
    print(br"=========================================")    
    
    bt_cfg = BacktestConfig(
        initial_capital=10_000.0,
        risk_per_trade=0.01,
        commission_rate=0.0004,
        slippage_rate=0.0002,
        max_leverage=10.0
    )
    
    ind_cfg = IndicatorConfig(fvg_min_gap_atr_mult=best_params["fvg_gap"])
    w = ScoreWeights(min_score_to_trade=best_params["min_score"])
    risk_cfg = RiskConfig(base_sl_atr_mult=best_params["atr_mult"])
    
    res = backtest_v2(df_micro, df_macro, bt=bt_cfg, ind_cfg=ind_cfg, w=w, risk_cfg=risk_cfg)
    
    stats = res["stats"]
    trades = res["trades"]
    
    print(f"🏁 Backtest Complete!")
    print(f"💰 Final Equity: ${stats.get('equity_final', 0):,.2f}")
    print(f"📈 Profit Factor: {stats.get('profit_factor', 0):.2f}")
    print(f"🎯 Win Rate: {stats.get('win_rate', 0)*100:.2f}%")
    print(f"📉 Max Drawdown: {stats.get('max_drawdown', 0)*100:.2f}%")
    print(f"✅ Total Trades: {stats.get('n_trades', 0)}")
    print(f"⚖️  Sharpe Ratio: {stats.get('sharpe', 0):.2f}")
    print(f"📈 Expectancy: ${stats.get('expectancy', 0):.2f}")
    print(f"📏 Avg R-Multiple: {stats.get('avg_r_multiple', 0):.2f}R")
    
    # print some of the trades
    if not trades.empty:
        print("\n📜 Last 5 Trades:")
        # Select important columns using correct names from the dictionary appended in backtest_v2
        display_trades = trades[['entry_time', 'exit_time', 'side', 'entry', 'exit', 'reason', 'pnl']].tail(5)
        print(display_trades.to_string(index=False))

if __name__ == "__main__":
    asyncio.run(run_optimization())
