"""
Diagnostic Deep Dive: تتبع المشكلة بالتفصيل
نحلل كل صفقة خاسرة ونكتشف السبب الدقيق
"""
import os
import pandas as pd
import numpy as np
import logging
from trading.backtesting_v2 import backtest_v2, BacktestConfig
from trading.technical_indicators import (
    IndicatorConfig, ScoreWeights, RiskConfig,
    SignalEngineV3_LiquidityTrap
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

import trading.backtesting_v2


def analyze_losing_trades_root_causes():
    """تحليل الأسباب الجذرية للصفقات الخاسرة"""

    symbol = "BTCUSDT"
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    micro_path = os.path.join(data_dir, f"{symbol}_5m_3M.parquet")
    macro_path = os.path.join(data_dir, f"{symbol}_1h_3M.parquet")

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

    # Patch
    trading.backtesting_v2.SignalEngineV2.generate_entry_signal = SignalEngineV3_LiquidityTrap.generate_entry_signal

    logger.info("Running backtest...")
    res = backtest_v2(
        df_micro, df_macro,
        bt=bt_cfg,
        ind_cfg=IndicatorConfig(),
        w=ScoreWeights(),
        risk_cfg=risk_cfg
    )

    trades_df = res['trades']

    print("\n" + "="*100)
    print("          🔬 DIAGNOSTIC DEEP DIVE: Root Cause Analysis of Losing Trades")
    print("="*100)

    # فصل الرابحة عن الخاسرة
    winners = trades_df[trades_df['pnl'] > 0]
    losers = trades_df[trades_df['pnl'] <= 0]

    print(f"\n📊 Dataset Overview:")
    print(f"   Total Trades: {len(trades_df)}")
    print(f"   Winners: {len(winners)} ({len(winners)/len(trades_df)*100:.1f}%)")
    print(f"   Losers: {len(losers)} ({len(losers)/len(trades_df)*100:.1f}%)")

    # 🔍 Problem 1: SL Distance Analysis
    print(f"\n\n🎯 PROBLEM 1: Stop Loss Distance")
    print("-" * 100)

    losers['sl_distance_pct'] = abs(losers['entry'] - losers['stop']) / losers['entry'] * 100
    winners['sl_distance_pct'] = abs(winners['entry'] - winners['stop']) / winners['entry'] * 100

    print(f"   Winners avg SL distance: {winners['sl_distance_pct'].mean():.3f}%")
    print(f"   Losers avg SL distance:  {losers['sl_distance_pct'].mean():.3f}%")
    print(f"   Difference: {winners['sl_distance_pct'].mean() - losers['sl_distance_pct'].mean():.3f}%")

    # تحليل: كم من الخاسرين لديهم SL ضيق جداً؟
    very_tight_sl = losers[losers['sl_distance_pct'] < 0.25]
    print(f"\n   ⚠️ Losers with VERY TIGHT SL (<0.25%): {len(very_tight_sl)} ({len(very_tight_sl)/len(losers)*100:.1f}%)")

    if len(very_tight_sl) > 0:
        print(f"      → Avg Loss for tight SL: {very_tight_sl['pnl'].mean():.2f}")
        print(f"      → These trades likely got stopped out by normal volatility/gaps")

    # 🔍 Problem 2: Gap Slippage Impact
    print(f"\n\n📉 PROBLEM 2: Gap Slippage Impact")
    print("-" * 100)

    # حساب actual loss vs expected loss
    if 'initial_risk' in losers.columns:
        losers['expected_loss'] = -losers['initial_risk']
        losers['actual_loss'] = losers['pnl']
        losers['slippage_impact'] = losers['actual_loss'] - losers['expected_loss']

        # فقط الخاسرون الذين ضربوا SL
        sl_losers = losers[losers['reason'] == 'SL']

        if len(sl_losers) > 0:
            avg_slippage = sl_losers['slippage_impact'].mean()
            print(f"   Avg slippage/gap impact: ${avg_slippage:.2f} per SL trade")

            # كم من الصفقات لديها slippage كبير؟
            high_slippage = sl_losers[sl_losers['slippage_impact'] < -20]
            print(f"   Trades with high slippage (>$20): {len(high_slippage)} ({len(high_slippage)/len(sl_losers)*100:.1f}%)")

    # 🔍 Problem 3: Entry Timing
    print(f"\n\n⏰ PROBLEM 3: Entry Timing Issues")
    print("-" * 100)

    losers['entry_time'] = pd.to_datetime(losers['entry_time'])
    losers['day_of_week'] = losers['entry_time'].dt.day_name()
    losers['hour'] = losers['entry_time'].dt.hour

    # أسوأ يوم
    worst_day_losses = losers.groupby('day_of_week')['pnl'].sum().sort_values()
    print(f"   Worst day for losses: {worst_day_losses.index[0]} (${worst_day_losses.iloc[0]:.2f})")

    thursday_losers = losers[losers['day_of_week'] == 'Thursday']
    print(f"   Thursday losers: {len(thursday_losers)} trades, ${thursday_losers['pnl'].sum():.2f} total loss")

    # أسوأ ساعة
    worst_hour_losses = losers.groupby('hour')['pnl'].sum().sort_values()
    print(f"\n   Worst 3 hours:")
    for i in range(min(3, len(worst_hour_losses))):
        hour = worst_hour_losses.index[i]
        loss = worst_hour_losses.iloc[i]
        count = len(losers[losers['hour'] == hour])
        print(f"      Hour {hour:02d}: {count} trades, ${loss:.2f}")

    # 🔍 Problem 4: Wrong Regime
    print(f"\n\n📈 PROBLEM 4: Wrong Market Regime")
    print("-" * 100)

    # تحليل: في أي ظروف تخسر الصفقات؟
    # نحتاج نحسب trend slope لكل صفقة

    print("   Analyzing market conditions at entry...")

    losers_with_regime = []
    for idx, trade in losers.head(50).iterrows():  # عينة من 50 صفقة
        try:
            entry_time = pd.to_datetime(trade['entry_time'])

            # Get data slice up to entry
            micro_slice = df_micro[:entry_time].tail(20)

            if len(micro_slice) >= 20:
                # حساب trend slope
                sma = micro_slice['close'].rolling(20).mean()
                if len(sma) > 0:
                    slope = (sma.iloc[-1] - sma.iloc[0]) / sma.iloc[0] * 100

                    losers_with_regime.append({
                        'trade_id': idx,
                        'pnl': trade['pnl'],
                        'slope': slope,
                        'side': trade['side']
                    })
        except Exception as e:
            continue

    if len(losers_with_regime) > 0:
        regime_df = pd.DataFrame(losers_with_regime)

        # Strong uptrend losers
        strong_up_losers = regime_df[regime_df['slope'] > 0.5]
        # Strong downtrend losers
        strong_dn_losers = regime_df[regime_df['slope'] < -0.5]
        # Ranging losers
        ranging_losers = regime_df[(regime_df['slope'] >= -0.5) & (regime_df['slope'] <= 0.5)]

        print(f"\n   Losers in STRONG UPTREND (slope >0.5%): {len(strong_up_losers)} ({len(strong_up_losers)/len(regime_df)*100:.1f}%)")
        print(f"   Losers in STRONG DOWNTREND (slope <-0.5%): {len(strong_dn_losers)} ({len(strong_dn_losers)/len(regime_df)*100:.1f}%)")
        print(f"   Losers in RANGING (|slope| <0.5%): {len(ranging_losers)} ({len(ranging_losers)/len(regime_df)*100:.1f}%)")

    # 🔍 Problem 5: Side Bias
    print(f"\n\n⚖️ PROBLEM 5: LONG vs SHORT Performance")
    print("-" * 100)

    long_losers = losers[losers['side'] == 'LONG']
    short_losers = losers[losers['side'] == 'SHORT']

    print(f"   LONG losers: {len(long_losers)} trades, ${long_losers['pnl'].sum():.2f}")
    print(f"   SHORT losers: {len(short_losers)} trades, ${short_losers['pnl'].sum():.2f}")

    long_win_rate = len(winners[winners['side'] == 'LONG']) / len(trades_df[trades_df['side'] == 'LONG']) * 100
    short_win_rate = len(winners[winners['side'] == 'SHORT']) / len(trades_df[trades_df['side'] == 'SHORT']) * 100

    print(f"\n   LONG Win Rate: {long_win_rate:.1f}%")
    print(f"   SHORT Win Rate: {short_win_rate:.1f}%")
    print(f"   → SHORT is {long_win_rate - short_win_rate:.1f}% worse")

    # 📋 SUMMARY & ROOT CAUSES
    print(f"\n\n" + "="*100)
    print("          💡 ROOT CAUSES SUMMARY")
    print("="*100)

    print("\n1. 🎯 STOP LOSS TOO TIGHT")
    print(f"   Problem: {len(very_tight_sl)}/{len(losers)} losers have SL <0.25%")
    print(f"   Impact: ${very_tight_sl['pnl'].sum() if len(very_tight_sl) > 0 else 0:.2f}")
    print(f"   Fix: Increase SL to 1.5× ATR (target: 0.35-0.45%)")

    print("\n2. ⏰ WRONG TIMING")
    print(f"   Problem: Thursday + Hours 10,11 are catastrophic")
    print(f"   Impact: ${thursday_losers['pnl'].sum():.2f} on Thursday alone")
    print(f"   Fix: Block trading on Thursday and hours [3,7,10,11,18]")

    if len(losers_with_regime) > 0:
        print("\n3. 📈 WRONG REGIME")
        strong_trend_losers = len(strong_up_losers) + len(strong_dn_losers) if 'strong_up_losers' in locals() else 0
        print(f"   Problem: {strong_trend_losers} losers in strong trends")
        print(f"   Fix: Add regime filter (avoid |slope| > 0.5%)")

    print("\n4. ⚖️ SHORT BIAS")
    print(f"   Problem: SHORT WR = {short_win_rate:.1f}% (vs LONG {long_win_rate:.1f}%)")
    print(f"   Fix: Disable SHORT or improve SHORT entry conditions")

    print("\n5. 📉 GAP SLIPPAGE")
    if 'avg_slippage' in locals():
        print(f"   Problem: Avg ${avg_slippage:.2f} slippage per SL hit")
        print(f"   Fix: Wider SL reduces frequency of SL hits")

    print("\n" + "="*100)
    print()


if __name__ == "__main__":
    analyze_losing_trades_root_causes()
