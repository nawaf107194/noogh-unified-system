import os
import pandas as pd
import logging
from prettytable import PrettyTable
from trading.backtesting_v2 import backtest_v2, BacktestConfig
from trading.technical_indicators import IndicatorConfig, ScoreWeights, RiskConfig, SignalEngineV3_LiquidityTrap

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Monkey patch backtest_v2 to use the new Engine
import trading.backtesting_v2
def monkey_patched_backtest(*args, **kwargs):
    # Save original generate_entry_signal
    original_func = trading.backtesting_v2.SignalEngineV2.generate_entry_signal
    try:
        trading.backtesting_v2.SignalEngineV2.generate_entry_signal = SignalEngineV3_LiquidityTrap.generate_entry_signal
        return backtest_v2(*args, **kwargs)
    finally:
        trading.backtesting_v2.SignalEngineV2.generate_entry_signal = original_func

def run_trap_test():
    symbol = "BTCUSDT"
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    micro_path = os.path.join(data_dir, f"{symbol}_5m_3M.parquet")
    macro_path = os.path.join(data_dir, f"{symbol}_1h_3M.parquet")
    
    if not os.path.exists(micro_path) or not os.path.exists(macro_path):
        logger.error("Data files not found. Please run download_history.py first.")
        return
        
    logger.info("Loading 3 months of historical data...")
    df_micro = pd.read_parquet(micro_path)
    df_macro = pd.read_parquet(macro_path)
    
    logger.info(f"Loaded {len(df_micro)} micro bars and {len(df_macro)} macro bars.")
    
    bt_cfg = BacktestConfig(
        initial_capital=10_000.0,
        risk_per_trade=0.01,
        commission_rate=0.0004,
        slippage_rate=0.0002
    )
    ind_cfg = IndicatorConfig()
    
    t = PrettyTable()
    t.field_names = ["Metric", "RRR=1.0", "RRR=1.2", "RRR=1.5"]
    t.align["Metric"] = "l"
    
    # RRR = 1.0
    logger.info("Running Trap Model (RRR=1.0)...")
    risk_cfg_10 = RiskConfig(min_rrr=1.0, tp2_mult=float('nan'), tp3_mult=float('nan'))
    res_10 = monkey_patched_backtest(df_micro, df_macro, bt=bt_cfg, ind_cfg=ind_cfg, w=ScoreWeights(), risk_cfg=risk_cfg_10)
    
    # RRR = 1.2
    logger.info("Running Trap Model (RRR=1.2)...")
    risk_cfg_12 = RiskConfig(min_rrr=1.2, tp2_mult=float('nan'), tp3_mult=float('nan'))
    res_12 = monkey_patched_backtest(df_micro, df_macro, bt=bt_cfg, ind_cfg=ind_cfg, w=ScoreWeights(), risk_cfg=risk_cfg_12)

    # RRR = 1.5
    logger.info("Running Trap Model (RRR=1.5)...")
    risk_cfg_15 = RiskConfig(min_rrr=1.5, tp2_mult=float('nan'), tp3_mult=float('nan'))
    res_15 = monkey_patched_backtest(df_micro, df_macro, bt=bt_cfg, ind_cfg=ind_cfg, w=ScoreWeights(), risk_cfg=risk_cfg_15)

    stats_10 = res_10['stats']
    stats_12 = res_12['stats']
    stats_15 = res_15['stats']
    
    t.add_row(["Win Rate", f"{stats_10.get('win_rate', 0)*100:.2f}%", f"{stats_12.get('win_rate', 0)*100:.2f}%", f"{stats_15.get('win_rate', 0)*100:.2f}%"])
    t.add_row(["Profit Factor", f"{stats_10.get('profit_factor', 0):.2f}", f"{stats_12.get('profit_factor', 0):.2f}", f"{stats_15.get('profit_factor', 0):.2f}"])
    t.add_row(["Sharpe Ratio", f"{stats_10.get('sharpe', 0):.2f}", f"{stats_12.get('sharpe', 0):.2f}", f"{stats_15.get('sharpe', 0):.2f}"])
    t.add_row(["Max Drawdown", f"{stats_10.get('max_drawdown', 0)*100:.2f}%", f"{stats_12.get('max_drawdown', 0)*100:.2f}%", f"{stats_15.get('max_drawdown', 0)*100:.2f}%"])
    t.add_row(["Expectancy", f"${stats_10.get('expectancy', 0):.2f}", f"${stats_12.get('expectancy', 0):.2f}", f"${stats_15.get('expectancy', 0):.2f}"])
    t.add_row(["Trades Count", stats_10.get('n_trades', 0), stats_12.get('n_trades', 0), stats_15.get('n_trades', 0)])
    t.add_row(["Final Equity", f"${stats_10.get('equity_final', 10000):,.2f}", f"${stats_12.get('equity_final', 10000):,.2f}", f"${stats_15.get('equity_final', 10000):,.2f}"])
    
    print("\n" + "=" * 60)
    print("        PURE LIQUIDITY TRAP MODEL TEST          ")
    print("=" * 60)
    print(t)
    print("=" * 60)

if __name__ == "__main__":
    run_trap_test()
