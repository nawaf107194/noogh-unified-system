"""
Cost Ablation Test: قياس تأثير العمولة والانزلاق
نشغل الباكتيست مع وبدون تكاليف لنعرف كم من الخسارة بسبب:
1. الإشارات السيئة (signal quality)
2. التكاليف (commission + slippage)
"""
import os
import pandas as pd
import logging
from prettytable import PrettyTable
from trading.backtesting_v2 import backtest_v2, BacktestConfig
from trading.technical_indicators import (
    IndicatorConfig, ScoreWeights, RiskConfig,
    SignalEngineV3_LiquidityTrap
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

import trading.backtesting_v2


def run_cost_ablation():
    symbol = "BTCUSDT"
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    micro_path = os.path.join(data_dir, f"{symbol}_5m_3M.parquet")
    macro_path = os.path.join(data_dir, f"{symbol}_1h_3M.parquet")

    if not os.path.exists(micro_path) or not os.path.exists(macro_path):
        logger.error("Data files not found.")
        return

    logger.info("Loading data...")
    df_micro = pd.read_parquet(micro_path)
    df_macro = pd.read_parquet(macro_path)

    risk_cfg = RiskConfig(min_rrr=1.5, tp2_mult=float('nan'), tp3_mult=float('nan'))

    # Patch signal engine
    trading.backtesting_v2.SignalEngineV2.generate_entry_signal = SignalEngineV3_LiquidityTrap.generate_entry_signal

    # Test 1: With full costs (baseline)
    logger.info("\n1️⃣ Testing WITH full costs...")
    bt_full_cost = BacktestConfig(
        initial_capital=10_000.0,
        risk_per_trade=0.01,
        commission_rate=0.0004,
        slippage_rate=0.0002
    )

    res_full = backtest_v2(
        df_micro, df_macro,
        bt=bt_full_cost,
        ind_cfg=IndicatorConfig(),
        w=ScoreWeights(),
        risk_cfg=risk_cfg
    )

    # Test 2: Zero costs (ideal)
    logger.info("\n2️⃣ Testing WITHOUT costs (commission=0, slippage=0)...")
    bt_zero_cost = BacktestConfig(
        initial_capital=10_000.0,
        risk_per_trade=0.01,
        commission_rate=0.0,
        slippage_rate=0.0
    )

    res_zero = backtest_v2(
        df_micro, df_macro,
        bt=bt_zero_cost,
        ind_cfg=IndicatorConfig(),
        w=ScoreWeights(),
        risk_cfg=risk_cfg
    )

    # Test 3: Commission only (no slippage)
    logger.info("\n3️⃣ Testing with commission only (slippage=0)...")
    bt_comm_only = BacktestConfig(
        initial_capital=10_000.0,
        risk_per_trade=0.01,
        commission_rate=0.0004,
        slippage_rate=0.0
    )

    res_comm = backtest_v2(
        df_micro, df_macro,
        bt=bt_comm_only,
        ind_cfg=IndicatorConfig(),
        w=ScoreWeights(),
        risk_cfg=risk_cfg
    )

    # Test 4: Slippage only (no commission)
    logger.info("\n4️⃣ Testing with slippage only (commission=0)...")
    bt_slip_only = BacktestConfig(
        initial_capital=10_000.0,
        risk_per_trade=0.01,
        commission_rate=0.0,
        slippage_rate=0.0002
    )

    res_slip = backtest_v2(
        df_micro, df_macro,
        bt=bt_slip_only,
        ind_cfg=IndicatorConfig(),
        w=ScoreWeights(),
        risk_cfg=risk_cfg
    )

    # Comparison Table
    t = PrettyTable()
    t.field_names = ["Metric", "Full Costs", "Zero Costs", "Comm Only", "Slip Only"]
    t.align["Metric"] = "l"

    s_full = res_full['stats']
    s_zero = res_zero['stats']
    s_comm = res_comm['stats']
    s_slip = res_slip['stats']

    eq_full = s_full.get('equity_final', 10000)
    eq_zero = s_zero.get('equity_final', 10000)
    eq_comm = s_comm.get('equity_final', 10000)
    eq_slip = s_slip.get('equity_final', 10000)

    pnl_full = eq_full - 10000
    pnl_zero = eq_zero - 10000
    pnl_comm = eq_comm - 10000
    pnl_slip = eq_slip - 10000

    t.add_row(["Trades",
               s_full.get('n_trades', 0),
               s_zero.get('n_trades', 0),
               s_comm.get('n_trades', 0),
               s_slip.get('n_trades', 0)])

    t.add_row(["Win Rate",
               f"{s_full.get('win_rate', 0)*100:.1f}%",
               f"{s_zero.get('win_rate', 0)*100:.1f}%",
               f"{s_comm.get('win_rate', 0)*100:.1f}%",
               f"{s_slip.get('win_rate', 0)*100:.1f}%"])

    t.add_row(["Profit Factor",
               f"{s_full.get('profit_factor', 0):.2f}",
               f"{s_zero.get('profit_factor', 0):.2f}",
               f"{s_comm.get('profit_factor', 0):.2f}",
               f"{s_slip.get('profit_factor', 0):.2f}"])

    t.add_row(["Avg R-Multiple",
               f"{s_full.get('avg_r_multiple', 0):.2f}",
               f"{s_zero.get('avg_r_multiple', 0):.2f}",
               f"{s_comm.get('avg_r_multiple', 0):.2f}",
               f"{s_slip.get('avg_r_multiple', 0):.2f}"])

    t.add_row(["Expectancy",
               f"${s_full.get('expectancy', 0):.2f}",
               f"${s_zero.get('expectancy', 0):.2f}",
               f"${s_comm.get('expectancy', 0):.2f}",
               f"${s_slip.get('expectancy', 0):.2f}"])

    t.add_row(["Final Equity",
               f"${eq_full:,.2f}",
               f"${eq_zero:,.2f}",
               f"${eq_comm:,.2f}",
               f"${eq_slip:,.2f}"])

    t.add_row(["Total PnL",
               f"${pnl_full:,.2f}",
               f"${pnl_zero:,.2f}",
               f"${pnl_comm:,.2f}",
               f"${pnl_slip:,.2f}"])

    print("\n" + "="*90)
    print("          💰 COST ABLATION: Impact of Commission & Slippage")
    print("="*90)
    print(t)
    print("="*90)

    # Analysis
    print("\n📊 COST BREAKDOWN:")

    cost_impact = pnl_zero - pnl_full
    comm_impact = pnl_zero - pnl_comm
    slip_impact = pnl_zero - pnl_slip

    print(f"\n   📍 Baseline (Full Costs): ${pnl_full:,.2f}")
    print(f"   ✨ Ideal (Zero Costs):    ${pnl_zero:,.2f}")
    print(f"\n   💸 Total cost impact:     ${cost_impact:,.2f} ({cost_impact/abs(pnl_full)*100 if pnl_full != 0 else 0:.1f}% of loss)")
    print(f"   📉 Commission impact:     ${comm_impact:,.2f}")
    print(f"   ⚡ Slippage impact:       ${slip_impact:,.2f}")

    print(f"\n   🔍 Cost per trade:")
    n_trades = s_full.get('n_trades', 1)
    print(f"      Total:      ${cost_impact/n_trades:.2f}")
    print(f"      Commission: ${comm_impact/n_trades:.2f}")
    print(f"      Slippage:   ${slip_impact/n_trades:.2f}")

    print("\n💡 DIAGNOSIS:")

    if pnl_zero > 0:
        print(f"   ✅ Strategy is PROFITABLE without costs (+${pnl_zero:,.2f})")
        print(f"   📌 Problem: التكاليف تقتل الميزة الإحصائية")
        print(f"   🎯 Solution: زيادة RRR أو تقليل عدد الصفقات أو استخدام exchange أرخص")
    elif pnl_zero > pnl_full * 0.5:  # تحسن كبير
        print(f"   🟡 Strategy is better without costs but still losing (${pnl_zero:,.2f})")
        print(f"   📌 Problem: التكاليف تضاعف الخسارة")
        print(f"   🎯 Solution: تحسين signal quality + تقليل التكاليف")
    else:
        print(f"   ❌ Strategy is losing even without costs (${pnl_zero:,.2f})")
        print(f"   📌 Problem: الإشارات نفسها سيئة - التكاليف ليست المشكلة الرئيسية")
        print(f"   🎯 Solution: إعادة النظر في signal logic والفلاتر")

    # R-Multiple comparison
    r_improvement = s_zero.get('avg_r_multiple', 0) - s_full.get('avg_r_multiple', 0)
    print(f"\n   📏 R-Multiple impact: {r_improvement:+.2f}R per trade")
    if r_improvement > 0.3:
        print(f"      التكاليف تأكل أكثر من 0.3R لكل صفقة - هذا كثير!")

    print()


if __name__ == "__main__":
    run_cost_ablation()
