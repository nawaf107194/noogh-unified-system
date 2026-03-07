import os
import pandas as pd
import logging
from prettytable import PrettyTable
from trading.backtesting_v2 import backtest_v2, BacktestConfig
from trading.technical_indicators import IndicatorConfig, ScoreWeights, RiskConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def run_ab_test():
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
    risk_cfg = RiskConfig(
        min_rrr=2.5,
        tp2_mult=float("nan"),
        tp3_mult=float("nan")
    )
    
    # ---------------------------------------------------------
    # VERSION A: Flow OFF
    # ---------------------------------------------------------
    logger.info("Running Version A: Flow OFF...")
    w_off = ScoreWeights(
        orderflow_impulse=0,
        cvd_trend=0,
        min_score_to_trade=85
    )
    res_a = backtest_v2(df_micro, df_macro, bt=bt_cfg, ind_cfg=ind_cfg, w=w_off, risk_cfg=risk_cfg)
    
    # ---------------------------------------------------------
    # VERSION B: Flow ON
    # ---------------------------------------------------------
    logger.info("Running Version B: Flow ON...")
    w_on = ScoreWeights(
        orderflow_impulse=30,
        cvd_trend=15,
        min_score_to_trade=85
    )
    res_b = backtest_v2(df_micro, df_macro, bt=bt_cfg, ind_cfg=ind_cfg, w=w_on, risk_cfg=risk_cfg)
    
    # ---------------------------------------------------------
    # PRINT RESULTS
    # ---------------------------------------------------------
    logger.info("Generating Report...")
    
    stats_a = res_a['stats']
    stats_b = res_b['stats']
    
    t = PrettyTable()
    t.field_names = ["Metric", "Version A (Delta OFF)", "Version B (Delta ON)"]
    t.align["Metric"] = "l"
    
    t.add_row(["Win Rate", f"{stats_a.get('win_rate', 0)*100:.2f}%", f"{stats_b.get('win_rate', 0)*100:.2f}%"])
    t.add_row(["Profit Factor", f"{stats_a.get('profit_factor', 0):.2f}", f"{stats_b.get('profit_factor', 0):.2f}"])
    t.add_row(["Sharpe Ratio", f"{stats_a.get('sharpe', 0):.2f}", f"{stats_b.get('sharpe', 0):.2f}"])
    t.add_row(["Max Drawdown", f"{stats_a.get('max_drawdown', 0)*100:.2f}%", f"{stats_b.get('max_drawdown', 0)*100:.2f}%"])
    t.add_row(["Expectancy", f"${stats_a.get('expectancy', 0):.2f}", f"${stats_b.get('expectancy', 0):.2f}"])
    t.add_row(["Avg PNL", f"${stats_a.get('avg_pnl', 0):.2f}", f"${stats_b.get('avg_pnl', 0):.2f}"])
    t.add_row(["Trades Count", stats_a.get('n_trades', 0), stats_b.get('n_trades', 0)])
    t.add_row(["Final Equity", f"${stats_a.get('equity_final', 10000):,.2f}", f"${stats_b.get('equity_final', 10000):,.2f}"])
    
    print("\n")
    print("=" * 60)
    print("        A/B TEST: ORDER FLOW VS TECHNICAL ONLY          ")
    print("=" * 60)
    print(t)
    print("=" * 60)

if __name__ == "__main__":
    run_ab_test()
