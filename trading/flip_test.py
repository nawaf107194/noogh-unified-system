"""
Flip Test: عكس جميع إشارات Liquidity Trap لاكتشاف خلل في logic الاتجاه
إذا تحسن الأداء = المشكلة في تحديد الاتجاه فقط
إذا ظل خاسر = المشكلة أعمق
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


class FlippedSignalEngine:
    """محرك إشارات معكوس - يعكس كل إشارات Liquidity Trap"""

    @staticmethod
    def generate_entry_signal(df_macro, df_micro, cfg, risk_cfg, **kwargs):
        # نستخدم نفس logic المصيدة (نتجاهل kwargs مثل w)
        original_signal = SignalEngineV3_LiquidityTrap.generate_entry_signal(
            df_macro, df_micro, cfg, risk_cfg
        )

        # نعكس الإشارة
        if original_signal['signal'] == 'LONG':
            flipped = original_signal.copy()
            flipped['signal'] = 'SHORT'
            # نعكس SL و entry
            entry = flipped['entry_price']
            sl = flipped['stop_loss']
            distance = abs(entry - sl)

            # SHORT: entry نفسه، SL فوق
            flipped['stop_loss'] = entry + distance

            # نعكس TP
            if 'target_prices' in flipped:
                tp1 = flipped['target_prices'].get('tp1')
                if tp1 and pd.notna(tp1):
                    tp_distance = abs(entry - tp1)
                    flipped['target_prices']['tp1'] = entry - tp_distance

            return flipped

        elif original_signal['signal'] == 'SHORT':
            flipped = original_signal.copy()
            flipped['signal'] = 'LONG'
            # نعكس SL و entry
            entry = flipped['entry_price']
            sl = flipped['stop_loss']
            distance = abs(entry - sl)

            # LONG: entry نفسه، SL تحت
            flipped['stop_loss'] = entry - distance

            # نعكس TP
            if 'target_prices' in flipped:
                tp1 = flipped['target_prices'].get('tp1')
                if tp1 and pd.notna(tp1):
                    tp_distance = abs(entry - tp1)
                    flipped['target_prices']['tp1'] = entry + tp_distance

            return flipped

        # إذا ما في إشارة، نرجع نفس الشي
        return original_signal


def run_flip_test():
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

    bt_cfg = BacktestConfig(
        initial_capital=10_000.0,
        risk_per_trade=0.01,
        commission_rate=0.0004,
        slippage_rate=0.0002
    )

    risk_cfg = RiskConfig(min_rrr=1.5, tp2_mult=float('nan'), tp3_mult=float('nan'))

    # Test 1: Original Trap
    logger.info("\n1️⃣ Testing Original Liquidity Trap...")
    trading.backtesting_v2.SignalEngineV2.generate_entry_signal = SignalEngineV3_LiquidityTrap.generate_entry_signal

    res_original = backtest_v2(
        df_micro, df_macro,
        bt=bt_cfg,
        ind_cfg=IndicatorConfig(),
        w=ScoreWeights(),
        risk_cfg=risk_cfg
    )

    # Test 2: Flipped Trap
    logger.info("\n2️⃣ Testing FLIPPED Liquidity Trap...")
    trading.backtesting_v2.SignalEngineV2.generate_entry_signal = FlippedSignalEngine.generate_entry_signal

    res_flipped = backtest_v2(
        df_micro, df_macro,
        bt=bt_cfg,
        ind_cfg=IndicatorConfig(),
        w=ScoreWeights(),
        risk_cfg=risk_cfg
    )

    # Comparison Table
    t = PrettyTable()
    t.field_names = ["Metric", "Original Trap", "FLIPPED Trap", "Delta"]
    t.align["Metric"] = "l"

    s_orig = res_original['stats']
    s_flip = res_flipped['stats']

    def delta(orig, flip, is_pct=False):
        diff = flip - orig
        if is_pct:
            return f"+{diff*100:.1f}%" if diff > 0 else f"{diff*100:.1f}%"
        return f"+{diff:.2f}" if diff > 0 else f"{diff:.2f}"

    n_orig = s_orig.get('n_trades', 0)
    n_flip = s_flip.get('n_trades', 0)
    wr_orig = s_orig.get('win_rate', 0)
    wr_flip = s_flip.get('win_rate', 0)
    pf_orig = s_orig.get('profit_factor', 0)
    pf_flip = s_flip.get('profit_factor', 0)
    eq_orig = s_orig.get('equity_final', 10000)
    eq_flip = s_flip.get('equity_final', 10000)
    pnl_orig = eq_orig - 10000
    pnl_flip = eq_flip - 10000

    t.add_row(["Trades", n_orig, n_flip, f"{n_flip - n_orig:+d}"])
    t.add_row(["Win Rate", f"{wr_orig*100:.1f}%", f"{wr_flip*100:.1f}%", delta(wr_orig, wr_flip, True)])
    t.add_row(["Profit Factor", f"{pf_orig:.2f}", f"{pf_flip:.2f}", delta(pf_orig, pf_flip)])
    t.add_row(["Sharpe Ratio", f"{s_orig.get('sharpe', 0):.2f}", f"{s_flip.get('sharpe', 0):.2f}",
               delta(s_orig.get('sharpe', 0), s_flip.get('sharpe', 0))])
    t.add_row(["Max Drawdown", f"{s_orig.get('max_drawdown', 0)*100:.1f}%",
               f"{s_flip.get('max_drawdown', 0)*100:.1f}%",
               delta(s_orig.get('max_drawdown', 0), s_flip.get('max_drawdown', 0), True)])
    t.add_row(["Expectancy", f"${s_orig.get('expectancy', 0):.2f}",
               f"${s_flip.get('expectancy', 0):.2f}",
               f"${s_flip.get('expectancy', 0) - s_orig.get('expectancy', 0):.2f}"])
    t.add_row(["Avg R-Multiple", f"{s_orig.get('avg_r_multiple', 0):.2f}",
               f"{s_flip.get('avg_r_multiple', 0):.2f}",
               delta(s_orig.get('avg_r_multiple', 0), s_flip.get('avg_r_multiple', 0))])
    t.add_row(["Final Equity", f"${eq_orig:,.2f}", f"${eq_flip:,.2f}", f"${eq_flip - eq_orig:+,.2f}"])
    t.add_row(["Total PnL", f"${pnl_orig:,.2f}", f"${pnl_flip:,.2f}", f"${pnl_flip - pnl_orig:+,.2f}"])

    print("\n" + "="*80)
    print("          🔄 FLIP TEST: Original vs Flipped Signals")
    print("="*80)
    print(t)
    print("="*80)

    # التحليل
    print("\n📊 ANALYSIS:")

    improvement = pnl_flip - pnl_orig
    pct_improvement = (improvement / abs(pnl_orig)) * 100 if pnl_orig != 0 else 0

    if pnl_flip > 0:
        print(f"   ✅ FLIPPED is PROFITABLE: ${pnl_flip:,.2f}")
        print(f"   🎯 Improvement: ${improvement:+,.2f} ({pct_improvement:+.1f}%)")
        print(f"\n   💡 DIAGNOSIS: المشكلة في تحديد الاتجاه!")
        print(f"      النموذج يكتشف الأماكن الصح لكن يدخل الاتجاه الغلط.")
        print(f"      الحل: عكس logic الدخول أو مراجعة شروط bullish/bearish trap.")
    elif improvement > abs(pnl_orig) * 0.3:  # تحسن بأكثر من 30%
        print(f"   🟡 FLIPPED is better but still losing: ${pnl_flip:,.2f}")
        print(f"   🎯 Improvement: ${improvement:+,.2f} ({pct_improvement:+.1f}%)")
        print(f"\n   💡 DIAGNOSIS: المشكلة جزئياً في الاتجاه")
        print(f"      في تحسن ملموس لكن ما يكفي. قد يحتاج تعديل logic + filters.")
    else:
        print(f"   ❌ FLIPPED is also losing: ${pnl_flip:,.2f}")
        print(f"   🎯 Change: ${improvement:+,.2f} ({pct_improvement:+.1f}%)")
        print(f"\n   💡 DIAGNOSIS: المشكلة ليست في الاتجاه")
        print(f"      النموذج لا يميز بين الصفقات الجيدة والسيئة.")
        print(f"      المشكلة في: timing, filters, market regime, أو signal quality.")

    print()


if __name__ == "__main__":
    run_flip_test()
