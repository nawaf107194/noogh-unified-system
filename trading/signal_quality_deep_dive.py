"""
Signal Quality Deep Dive: مقارنة features الصفقات الرابحة vs الخاسرة
نكتشف:
1. ما الفرق بين الصفقات الرابحة والخاسرة؟
2. هل في features تميز الصفقات الجيدة؟
3. هل يمكن إضافة فلتر لتحسين الأداء؟
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


def analyze_signal_features(df_micro, df_macro, trades_df):
    """تحليل features للصفقات الرابحة vs الخاسرة"""

    features_list = []

    for _, trade in trades_df.iterrows():
        entry_time = pd.to_datetime(trade['entry_time'])

        # Get micro slice up to entry
        micro_slice = df_micro[:entry_time]
        if len(micro_slice) < 50:
            continue

        # Get macro slice
        macro_slice = df_macro[:entry_time]
        if len(macro_slice) < 20:
            continue

        # Extract features at entry time
        features = {}

        # 1. Simple ATR calculation (average range over last 14 bars)
        recent_bars = micro_slice.iloc[-14:]
        if len(recent_bars) >= 14:
            tr = recent_bars[['high', 'low', 'close']].copy()
            tr['h_l'] = tr['high'] - tr['low']
            tr['h_pc'] = abs(tr['high'] - tr['close'].shift(1))
            tr['l_pc'] = abs(tr['low'] - tr['close'].shift(1))
            tr['tr'] = tr[['h_l', 'h_pc', 'l_pc']].max(axis=1)
            atr = tr['tr'].mean()

            features['atr'] = atr
            features['atr_pct'] = (atr / micro_slice['close'].iloc[-1] * 100) if atr > 0 else np.nan
        else:
            features['atr'] = np.nan
            features['atr_pct'] = np.nan

        # 2. Simple trend calculation (slope of SMA)
        if len(micro_slice) >= 20:
            sma_20 = micro_slice['close'].rolling(20).mean().iloc[-20:]
            if len(sma_20) > 1:
                slope = (sma_20.iloc[-1] - sma_20.iloc[0]) / sma_20.iloc[0] * 100
                features['trend_slope_pct'] = slope
            else:
                features['trend_slope_pct'] = np.nan
        else:
            features['trend_slope_pct'] = np.nan

        # 3. Price position relative to recent highs/lows
        recent_20 = micro_slice.iloc[-20:]
        if len(recent_20) >= 20:
            high_20 = recent_20['high'].max()
            low_20 = recent_20['low'].min()
            close = micro_slice['close'].iloc[-1]
            price_position = (close - low_20) / (high_20 - low_20) if (high_20 - low_20) > 0 else 0.5
            features['price_position_pct'] = price_position * 100
        else:
            features['price_position_pct'] = np.nan

        # 4. Recent price action
        recent_bars = micro_slice.iloc[-10:]
        features['avg_body_pct'] = (abs(recent_bars['close'] - recent_bars['open']) / recent_bars['open'] * 100).mean()
        features['avg_range_pct'] = ((recent_bars['high'] - recent_bars['low']) / recent_bars['low'] * 100).mean()

        # 5. Volume (if available)
        if 'volume' in micro_slice.columns and len(micro_slice) >= 20:
            features['volume_ratio'] = micro_slice['volume'].iloc[-1] / micro_slice['volume'].iloc[-20:].mean()
        else:
            features['volume_ratio'] = np.nan

        # 6. Distance to SL (risk)
        entry = trade['entry']
        sl = trade['stop']
        features['sl_distance_pct'] = abs(entry - sl) / entry * 100

        # 7. Side
        features['side'] = trade['side']

        # 8. Target
        features['is_win'] = trade['pnl'] > 0
        features['pnl'] = trade['pnl']
        features['r_multiple'] = trade.get('r_multiple', np.nan)

        features_list.append(features)

    return pd.DataFrame(features_list)


def run_signal_quality_analysis():
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

    if len(trades_df) == 0:
        print("No trades found!")
        return

    logger.info("Extracting features...")
    features_df = analyze_signal_features(df_micro, df_macro, trades_df)

    if len(features_df) == 0:
        print("Could not extract features!")
        return

    print("\n" + "="*80)
    print("          🔬 SIGNAL QUALITY DEEP DIVE: Winners vs Losers")
    print("="*80)

    wins = features_df[features_df['is_win'] == True]
    losses = features_df[features_df['is_win'] == False]

    print(f"\n📊 Sample Size:")
    print(f"   Winners: {len(wins)}")
    print(f"   Losers:  {len(losses)}")

    # Compare numerical features
    numerical_features = ['atr_pct', 'trend_slope_pct', 'price_position_pct', 'avg_body_pct',
                          'avg_range_pct', 'volume_ratio', 'sl_distance_pct']

    print(f"\n📈 Feature Comparison (Winners vs Losers):")
    print(f"\n{'Feature':<20} {'Winners':>12} {'Losers':>12} {'Diff':>12} {'Significant?':>15}")
    print("-" * 80)

    for feat in numerical_features:
        if feat not in features_df.columns:
            continue

        win_mean = wins[feat].mean()
        loss_mean = losses[feat].mean()
        diff = win_mean - loss_mean
        diff_pct = (diff / loss_mean * 100) if loss_mean != 0 and not np.isnan(loss_mean) else np.nan

        # Simple significance test (>20% difference)
        is_significant = abs(diff_pct) > 20 if not np.isnan(diff_pct) else False

        sig_marker = "⭐" if is_significant else ""

        print(f"{feat:<20} {win_mean:>12.2f} {loss_mean:>12.2f} {diff:>12.2f} {sig_marker:>15}")

    # Categorical features
    print(f"\n📊 Side Analysis:")
    side_win_rate = features_df.groupby('side')['is_win'].mean() * 100
    for side, wr in side_win_rate.items():
        count = len(features_df[features_df['side'] == side])
        print(f"   {side:<6}: {wr:>5.1f}% WR ({count} trades)")

    # Key insights
    print(f"\n\n💡 KEY INSIGHTS:")

    # 1. ATR insight
    if 'atr_pct' in features_df.columns:
        win_atr = wins['atr_pct'].mean()
        loss_atr = losses['atr_pct'].mean()
        if not np.isnan(win_atr) and not np.isnan(loss_atr):
            if win_atr < loss_atr * 0.8:
                print(f"   📉 Winners happen in LOWER volatility ({win_atr:.2f}% vs {loss_atr:.2f}%)")
                print(f"      💡 Filter: تجنب الدخول عند ATR > {loss_atr:.2f}%")
            elif win_atr > loss_atr * 1.2:
                print(f"   📈 Winners happen in HIGHER volatility ({win_atr:.2f}% vs {loss_atr:.2f}%)")
                print(f"      💡 Filter: تجنب الدخول عند ATR < {win_atr:.2f}%")

    # 2. Trend strength insight
    if 'trend_slope_pct' in features_df.columns:
        win_slope = wins['trend_slope_pct'].mean()
        loss_slope = losses['trend_slope_pct'].mean()
        if not np.isnan(win_slope) and not np.isnan(loss_slope):
            if abs(win_slope - loss_slope) > 0.5:
                better = "trending up" if win_slope > loss_slope else "trending down/flat"
                print(f"   📊 Winners happen in {better} market (slope {win_slope:.2f}% vs {loss_slope:.2f}%)")
                if win_slope > 0.5:
                    print(f"      💡 Filter: ادخل فقط في uptrend (slope > 0.5%)")
                elif win_slope < -0.5:
                    print(f"      💡 Filter: ادخل فقط في downtrend (slope < -0.5%)")

    # 3. SL distance
    if 'sl_distance_pct' in features_df.columns:
        win_sl = wins['sl_distance_pct'].mean()
        loss_sl = losses['sl_distance_pct'].mean()
        if not np.isnan(win_sl) and not np.isnan(loss_sl):
            if abs(win_sl - loss_sl) > 0.1:
                print(f"   🎯 Winners have {'wider' if win_sl > loss_sl else 'tighter'} SL ({win_sl:.2f}% vs {loss_sl:.2f}%)")
                if win_sl > loss_sl * 1.2:
                    print(f"      💡 الستوب الحالي ضيق جداً - جرب زيادته")

    # 4. Side bias
    if len(side_win_rate) > 1:
        best_side = side_win_rate.idxmax()
        worst_side = side_win_rate.idxmin()
        diff = side_win_rate[best_side] - side_win_rate[worst_side]
        if diff > 10:
            print(f"   ⚖️ {best_side} أفضل من {worst_side} بـ {diff:.1f}%")
            print(f"      💡 فكّر في التركيز على {best_side} فقط أو تحسين شروط {worst_side}")

    # Correlation analysis
    print(f"\n\n🔗 Feature Correlation with PnL:")
    correlations = features_df[numerical_features + ['pnl']].corr()['pnl'].drop('pnl').sort_values(ascending=False)
    print(correlations.to_string())

    print(f"\n   الـ features الأكثر ارتباطاً (موجب أو سالب) قد تكون useful كـ filters")

    print("\n" + "="*80)
    print()


if __name__ == "__main__":
    run_signal_quality_analysis()
