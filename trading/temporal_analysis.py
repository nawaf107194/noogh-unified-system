"""
Temporal Analysis: تحليل توزيع الخسائر زمنياً
نكتشف:
1. هل الخسائر متجمعة في فترات معينة؟
2. هل في regime يدمر الحساب؟
3. متى يحدث معظم الصفقات الخاسرة؟
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


def run_temporal_analysis():
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

    # Patch signal engine
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
    equity_curve = res.get('equity_curve', pd.Series())

    if len(trades_df) == 0:
        print("No trades found!")
        return

    # Convert to datetime
    trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
    trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])

    print("\n" + "="*80)
    print("          📅 TEMPORAL ANALYSIS: When Do Losses Occur?")
    print("="*80)

    # 1. Monthly breakdown
    print("\n📊 Monthly Performance:")
    trades_df['month'] = trades_df['entry_time'].dt.to_period('M')

    agg_dict = {'pnl': ['count', 'sum', 'mean']}
    if 'r_multiple' in trades_df.columns:
        agg_dict['r_multiple'] = 'mean'

    monthly = trades_df.groupby('month').agg(agg_dict).round(2)

    if 'r_multiple' in trades_df.columns:
        monthly.columns = ['Trades', 'Total PnL', 'Avg PnL', 'Avg R']
    else:
        monthly.columns = ['Trades', 'Total PnL', 'Avg PnL']

    wins_by_month = trades_df[trades_df['pnl'] > 0].groupby('month').size()
    monthly['Wins'] = wins_by_month
    monthly['Win Rate'] = (monthly['Wins'] / monthly['Trades'] * 100).fillna(0).round(1)

    print(monthly.to_string())

    # Find worst month
    worst_month = monthly['Total PnL'].idxmin()
    print(f"\n   🔴 Worst month: {worst_month} (${monthly.loc[worst_month, 'Total PnL']:.2f})")

    # 2. Weekly breakdown
    print("\n\n📅 Weekly Performance:")
    trades_df['week'] = trades_df['entry_time'].dt.to_period('W')

    agg_dict_weekly = {'pnl': ['count', 'sum']}
    if 'r_multiple' in trades_df.columns:
        agg_dict_weekly['r_multiple'] = 'mean'

    weekly = trades_df.groupby('week').agg(agg_dict_weekly).round(2)

    if 'r_multiple' in trades_df.columns:
        weekly.columns = ['Trades', 'Total PnL', 'Avg R']
    else:
        weekly.columns = ['Trades', 'Total PnL']

    # Show worst weeks
    print("\n   🔴 Worst 5 weeks:")
    worst_weeks = weekly.nsmallest(5, 'Total PnL')
    print(worst_weeks.to_string())

    # 3. Day of week analysis
    print("\n\n📆 Day of Week Analysis:")
    trades_df['day_of_week'] = trades_df['entry_time'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    agg_dict_dow = {'pnl': ['count', 'sum', 'mean']}
    if 'r_multiple' in trades_df.columns:
        agg_dict_dow['r_multiple'] = 'mean'

    dow = trades_df.groupby('day_of_week').agg(agg_dict_dow).round(2)

    if 'r_multiple' in trades_df.columns:
        dow.columns = ['Trades', 'Total PnL', 'Avg PnL', 'Avg R']
    else:
        dow.columns = ['Trades', 'Total PnL', 'Avg PnL']

    wins_by_dow = trades_df[trades_df['pnl'] > 0].groupby('day_of_week').size()
    dow['Win Rate'] = (wins_by_dow / dow['Trades'] * 100).fillna(0).round(1)

    # Reorder by day
    dow = dow.reindex([d for d in day_order if d in dow.index])
    print(dow.to_string())

    # 4. Hour of day analysis
    print("\n\n🕐 Hour of Day Analysis:")
    trades_df['hour'] = trades_df['entry_time'].dt.hour

    agg_dict_hourly = {'pnl': ['count', 'sum']}
    if 'r_multiple' in trades_df.columns:
        agg_dict_hourly['r_multiple'] = 'mean'

    hourly = trades_df.groupby('hour').agg(agg_dict_hourly).round(2)

    if 'r_multiple' in trades_df.columns:
        hourly.columns = ['Trades', 'Total PnL', 'Avg R']
    else:
        hourly.columns = ['Trades', 'Total PnL']

    wins_by_hour = trades_df[trades_df['pnl'] > 0].groupby('hour').size()
    hourly['Win Rate'] = (wins_by_hour / hourly['Trades'] * 100).fillna(0).round(1)

    print(hourly.to_string())

    best_hours = hourly.nlargest(3, 'Total PnL').index.tolist()
    worst_hours = hourly.nsmallest(3, 'Total PnL').index.tolist()
    print(f"\n   🟢 Best hours: {best_hours}")
    print(f"   🔴 Worst hours: {worst_hours}")

    # 5. Drawdown periods
    if len(equity_curve) > 0:
        print("\n\n📉 Equity Curve Analysis:")
        equity_curve = equity_curve.sort_index()
        peak = equity_curve.expanding().max()
        drawdown = (peak - equity_curve) / peak * 100

        max_dd = drawdown.max()
        max_dd_date = drawdown.idxmax()

        print(f"   Max Drawdown: {max_dd:.1f}%")
        print(f"   Max DD Date: {max_dd_date}")

        # Find underwater periods (drawdown > 10%)
        underwater = drawdown[drawdown > 10]
        if len(underwater) > 0:
            print(f"\n   🌊 Underwater periods (DD > 10%): {len(underwater)} bars")
            print(f"      First: {underwater.index[0]}")
            print(f"      Last:  {underwater.index[-1]}")

    # 6. Losing streak analysis
    print("\n\n🔄 Streak Analysis:")
    trades_df['is_win'] = trades_df['pnl'] > 0

    # Calculate streaks
    trades_df['streak_id'] = (trades_df['is_win'] != trades_df['is_win'].shift()).cumsum()
    streaks = trades_df.groupby('streak_id').agg({
        'is_win': ['first', 'size'],
        'pnl': 'sum',
        'entry_time': 'first'
    })
    streaks.columns = ['is_win', 'length', 'total_pnl', 'start_date']

    losing_streaks = streaks[~streaks['is_win']]
    if len(losing_streaks) > 0:
        max_losing_streak = losing_streaks['length'].max()
        worst_streak = losing_streaks.nsmallest(1, 'total_pnl').iloc[0]

        print(f"   Max losing streak: {max_losing_streak} trades")
        print(f"   Worst streak loss: ${worst_streak['total_pnl']:.2f} ({worst_streak['length']} trades)")
        print(f"      Started: {worst_streak['start_date']}")

    # 7. Volatility correlation
    print("\n\n📊 Trade Frequency Over Time:")
    trades_per_week = trades_df.groupby('week').size()
    print(f"   Average: {trades_per_week.mean():.1f} trades/week")
    print(f"   Max:     {trades_per_week.max()} trades/week")
    print(f"   Min:     {trades_per_week.min()} trades/week")

    # Find quiet and active periods
    quiet_weeks = trades_per_week[trades_per_week < trades_per_week.mean() * 0.5]
    active_weeks = trades_per_week[trades_per_week > trades_per_week.mean() * 1.5]

    if len(quiet_weeks) > 0:
        print(f"\n   🔕 Quiet weeks (<50% avg): {len(quiet_weeks)}")
    if len(active_weeks) > 0:
        print(f"   📢 Active weeks (>150% avg): {len(active_weeks)}")

    print("\n" + "="*80)

    # DIAGNOSIS
    print("\n💡 TEMPORAL DIAGNOSIS:")

    # Check if losses concentrated in specific period
    monthly_losses = monthly[monthly['Total PnL'] < 0]
    if len(monthly_losses) > 0:
        worst_month_pct = abs(monthly.loc[worst_month, 'Total PnL']) / abs(trades_df['pnl'].sum()) * 100
        if worst_month_pct > 40:
            print(f"   ⚠️ {worst_month_pct:.0f}% من الخسارة في شهر واحد ({worst_month})")
            print(f"      المشكلة: regime-specific - النموذج يعمل سيء في فترات معينة")
        else:
            print(f"   ℹ️ الخسائر موزعة عبر الأشهر - ليست مشكلة regime واحد")

    # Check day of week pattern
    dow_variance = dow['Total PnL'].std()
    if dow_variance > 500:
        print(f"   📅 في تباين كبير بين أيام الأسبوع - قد يحتاج filter زمني")

    # Check hour pattern
    if len(worst_hours) > 0:
        worst_hour_pnl = hourly.loc[worst_hours, 'Total PnL'].sum()
        if abs(worst_hour_pnl) > abs(trades_df['pnl'].sum()) * 0.3:
            print(f"   🕐 {abs(worst_hour_pnl)/abs(trades_df['pnl'].sum())*100:.0f}% من الخسارة في ساعات معينة: {worst_hours}")
            print(f"      التوصية: تجنب التداول في هذه الساعات")

    print()


if __name__ == "__main__":
    run_temporal_analysis()
