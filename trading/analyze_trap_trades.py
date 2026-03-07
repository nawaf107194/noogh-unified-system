"""
Detailed trade analysis for liquidity trap model
Analyzes individual trades to identify patterns in losses
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

# Monkey patch
import trading.backtesting_v2
def monkey_patched_backtest(*args, **kwargs):
    original_func = trading.backtesting_v2.SignalEngineV2.generate_entry_signal
    try:
        trading.backtesting_v2.SignalEngineV2.generate_entry_signal = SignalEngineV3_LiquidityTrap.generate_entry_signal
        return backtest_v2(*args, **kwargs)
    finally:
        trading.backtesting_v2.SignalEngineV2.generate_entry_signal = original_func


def analyze_trades():
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

    logger.info("Running backtest...")
    res = monkey_patched_backtest(df_micro, df_macro, bt=bt_cfg, ind_cfg=IndicatorConfig(),
                                   w=ScoreWeights(), risk_cfg=risk_cfg)

    trades_df = res['trades']

    if len(trades_df) == 0:
        print("No trades found!")
        return

    # Analysis
    print("\n" + "="*80)
    print("TRADE ANALYSIS FOR LIQUIDITY TRAP MODEL")
    print("="*80)

    wins = trades_df[trades_df['pnl'] > 0]
    losses = trades_df[trades_df['pnl'] <= 0]

    print(f"\n📊 Basic Stats:")
    print(f"   Total Trades: {len(trades_df)}")
    print(f"   Wins: {len(wins)} ({len(wins)/len(trades_df)*100:.1f}%)")
    print(f"   Losses: {len(losses)} ({len(losses)/len(trades_df)*100:.1f}%)")

    print(f"\n💰 PnL Distribution:")
    print(f"   Total PnL: ${trades_df['pnl'].sum():.2f}")
    print(f"   Avg Win: ${wins['pnl'].mean():.2f}" if len(wins) > 0 else "   Avg Win: N/A")
    print(f"   Avg Loss: ${losses['pnl'].mean():.2f}" if len(losses) > 0 else "   Avg Loss: N/A")
    print(f"   Largest Win: ${wins['pnl'].max():.2f}" if len(wins) > 0 else "   Largest Win: N/A")
    print(f"   Largest Loss: ${losses['pnl'].min():.2f}" if len(losses) > 0 else "   Largest Loss: N/A")

    print(f"\n📈 Exit Reasons:")
    exit_counts = trades_df['reason'].value_counts()
    for reason, count in exit_counts.items():
        pct = count / len(trades_df) * 100
        reason_pnl = trades_df[trades_df['reason'] == reason]['pnl'].sum()
        print(f"   {reason}: {count} ({pct:.1f}%) - Total PnL: ${reason_pnl:.2f}")

    print(f"\n🎯 Side Analysis:")
    for side in ['LONG', 'SHORT']:
        side_trades = trades_df[trades_df['side'] == side]
        if len(side_trades) > 0:
            side_wins = side_trades[side_trades['pnl'] > 0]
            wr = len(side_wins) / len(side_trades) * 100
            total_pnl = side_trades['pnl'].sum()
            print(f"   {side}: {len(side_trades)} trades, WR={wr:.1f}%, Total PnL=${total_pnl:.2f}")

    # Calculate R-multiples (CORRECT method using initial_risk)
    if 'initial_risk' in trades_df.columns:
        valid_risk = trades_df['initial_risk'] > 0
        trades_df['r_multiple'] = 0.0
        trades_df.loc[valid_risk, 'r_multiple'] = trades_df.loc[valid_risk, 'pnl'] / trades_df.loc[valid_risk, 'initial_risk']
    else:
        # Fallback (old method - less accurate)
        trades_df['risk'] = abs(trades_df['entry'] - trades_df['stop'])
        trades_df['r_multiple'] = trades_df['pnl'] / (trades_df['risk'] * trades_df['qty'])

    print(f"\n📏 R-Multiple Analysis (CORRECTED):")
    print(f"   Average R: {trades_df['r_multiple'].mean():.2f}")
    print(f"   Median R: {trades_df['r_multiple'].median():.2f}")
    print(f"   R Distribution:")
    print(f"      R > 2: {len(trades_df[trades_df['r_multiple'] > 2])} trades ({len(trades_df[trades_df['r_multiple'] > 2])/len(trades_df)*100:.1f}%)")
    print(f"      R > 1: {len(trades_df[trades_df['r_multiple'] > 1])} trades ({len(trades_df[trades_df['r_multiple'] > 1])/len(trades_df)*100:.1f}%)")
    print(f"      0 < R < 1: {len(trades_df[(trades_df['r_multiple'] > 0) & (trades_df['r_multiple'] <= 1)])} trades ({len(trades_df[(trades_df['r_multiple'] > 0) & (trades_df['r_multiple'] <= 1)])/len(trades_df)*100:.1f}%)")
    print(f"      -1 < R < 0: {len(trades_df[(trades_df['r_multiple'] < 0) & (trades_df['r_multiple'] >= -1)])} trades ({len(trades_df[(trades_df['r_multiple'] < 0) & (trades_df['r_multiple'] >= -1)])/len(trades_df)*100:.1f}%)")
    print(f"      R < -1: {len(trades_df[trades_df['r_multiple'] < -1])} trades ({len(trades_df[trades_df['r_multiple'] < -1])/len(trades_df)*100:.1f}%)")

    # Save detailed trades to CSV for inspection
    output_path = os.path.join(data_dir, "trap_trades_detailed.csv")
    trades_df.to_csv(output_path, index=False)
    print(f"\n💾 Detailed trades saved to: {output_path}")

    # Show worst 10 trades
    print(f"\n❌ Worst 10 Trades:")
    worst = trades_df.nsmallest(10, 'pnl')[['entry_time', 'side', 'entry', 'exit', 'stop', 'reason', 'pnl', 'r_multiple']]
    print(worst.to_string(index=False))

    # Show best 10 trades
    print(f"\n✅ Best 10 Trades:")
    best = trades_df.nlargest(10, 'pnl')[['entry_time', 'side', 'entry', 'exit', 'stop', 'reason', 'pnl', 'r_multiple']]
    print(best.to_string(index=False))

    print("\n" + "="*80)


if __name__ == "__main__":
    analyze_trades()
