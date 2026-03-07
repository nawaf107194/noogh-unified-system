"""
Compare SignalEngineV2 (base) vs SignalEngineV3_LiquidityTrap
"""
import os
import pandas as pd
import logging
from prettytable import PrettyTable
from trading.backtesting_v2 import backtest_v2, BacktestConfig
from trading.technical_indicators import (
    IndicatorConfig, ScoreWeights, RiskConfig,
    SignalEngineV2, SignalEngineV3_LiquidityTrap
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

import trading.backtesting_v2


def run_comparison():
    symbol = "BTCUSDT"
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    micro_path = os.path.join(data_dir, f"{symbol}_5m_3M.parquet")
    macro_path = os.path.join(data_dir, f"{symbol}_1h_3M.parquet")

    if not os.path.exists(micro_path) or not os.path.exists(macro_path):
        logger.error("Data files not found.")
        return

    logger.info("Loading 3 months of data...")
    df_micro = pd.read_parquet(micro_path)
    df_macro = pd.read_parquet(macro_path)

    logger.info(f"Loaded {len(df_micro)} micro bars, {len(df_macro)} macro bars")

    bt_cfg = BacktestConfig(
        initial_capital=10_000.0,
        risk_per_trade=0.01,
        commission_rate=0.0004,
        slippage_rate=0.0002
    )

    # Test 1: Base SignalEngineV2
    logger.info("\n1️⃣ Testing Base SignalEngineV2...")
    trading.backtesting_v2.SignalEngineV2.generate_entry_signal = SignalEngineV2.generate_entry_signal

    res_v2 = backtest_v2(
        df_micro, df_macro,
        bt=bt_cfg,
        ind_cfg=IndicatorConfig(),
        w=ScoreWeights(),
        risk_cfg=RiskConfig(min_rrr=1.5, tp2_mult=float('nan'), tp3_mult=float('nan'))
    )

    # Test 2: Liquidity Trap Model
    logger.info("\n2️⃣ Testing Liquidity Trap Model...")
    trading.backtesting_v2.SignalEngineV2.generate_entry_signal = SignalEngineV3_LiquidityTrap.generate_entry_signal

    res_trap = backtest_v2(
        df_micro, df_macro,
        bt=bt_cfg,
        ind_cfg=IndicatorConfig(),
        w=ScoreWeights(),
        risk_cfg=RiskConfig(min_rrr=1.5, tp2_mult=float('nan'), tp3_mult=float('nan'))
    )

    # Comparison Table
    t = PrettyTable()
    t.field_names = ["Metric", "Base V2", "Liquidity Trap"]
    t.align["Metric"] = "l"

    s_v2 = res_v2['stats']
    s_trap = res_trap['stats']

    t.add_row(["Trades", s_v2.get('n_trades', 0), s_trap.get('n_trades', 0)])
    t.add_row(["Win Rate", f"{s_v2.get('win_rate', 0)*100:.1f}%", f"{s_trap.get('win_rate', 0)*100:.1f}%"])
    t.add_row(["Profit Factor", f"{s_v2.get('profit_factor', 0):.2f}", f"{s_trap.get('profit_factor', 0):.2f}"])
    t.add_row(["Sharpe Ratio", f"{s_v2.get('sharpe', 0):.2f}", f"{s_trap.get('sharpe', 0):.2f}"])
    t.add_row(["Max Drawdown", f"{s_v2.get('max_drawdown', 0)*100:.1f}%", f"{s_trap.get('max_drawdown', 0)*100:.1f}%"])
    t.add_row(["Expectancy", f"${s_v2.get('expectancy', 0):.2f}", f"${s_trap.get('expectancy', 0):.2f}"])
    t.add_row(["Avg R-Multiple", f"{s_v2.get('avg_r_multiple', 0):.2f}", f"{s_trap.get('avg_r_multiple', 0):.2f}"])
    t.add_row(["Final Equity", f"${s_v2.get('equity_final', 10000):,.2f}", f"${s_trap.get('equity_final', 10000):,.2f}"])
    t.add_row(["Total PnL", f"${s_v2.get('equity_final', 10000) - 10000:,.2f}",
               f"${s_trap.get('equity_final', 10000) - 10000:,.2f}"])

    print("\n" + "="*70)
    print("          ENGINE COMPARISON: V2 vs LIQUIDITY TRAP")
    print("="*70)
    print(t)
    print("="*70)

    # Determine winner
    pnl_v2 = s_v2.get('equity_final', 10000) - 10000
    pnl_trap = s_trap.get('equity_final', 10000) - 10000

    print("\n🏆 VERDICT:")
    if pnl_v2 > pnl_trap:
        print(f"   Base V2 wins by ${abs(pnl_v2 - pnl_trap):.2f}")
    elif pnl_trap > pnl_v2:
        print(f"   Liquidity Trap wins by ${abs(pnl_trap - pnl_v2):.2f}")
    else:
        print("   Tie!")

    if pnl_v2 < 0 and pnl_trap < 0:
        print("   ⚠️ WARNING: Both strategies are losing money!")
    print()


if __name__ == "__main__":
    run_comparison()
