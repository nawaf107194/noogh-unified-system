# Macro Regime Detector
# Detects market regime: Trending, Ranging, Volatile

import numpy as np
import pandas as pd
from typing import Dict, Literal

from noogh.trading.technical_indicators import TechnicalIndicatorsV2

class RegimeDetector:
    """
    Advanced market regime detection using:
    - ADX (Trend strength)
    - ATR Ratio (Volatility)
    - Hurst Exponent (Persistence)
    - VIX Proxy (Fear gauge)
    """

    REGIMES = Literal['TRENDING_BULL', 'TRENDING_BEAR', 'RANGING', 'VOLATILE']

    @staticmethod
    def detect_regime(df_daily: pd.DataFrame, df_1h: pd.DataFrame) -> Dict[str, any]:
        """
        Detect current market regime.

        Args:
            df_daily: Daily candles for macro context
            df_1h: 1H candles for recent behavior

        Returns:
            Dict with regime, confidence, and regime-specific parameters
        """
        # 1. Trend Strength (ADX)
        adx = TechnicalIndicatorsV2.adx(df_1h, period=14)
        adx_current = adx.iloc[-1]
        trend_strength = 'STRONG' if adx_current > 30 else 'WEAK'

        # 2. Volatility Regime (ATR Ratio)
        atr_14 = TechnicalIndicatorsV2.atr(df_1h, 14)
        atr_50 = TechnicalIndicatorsV2.atr(df_1h, 50)
        atr_ratio = atr_14.iloc[-1] / atr_50.iloc[-1]
        volatility_regime = 'HIGH' if atr_ratio > 1.5 else 'LOW' if atr_ratio < 0.7 else 'NORMAL'

        # 3. Hurst Exponent (Trend persistence)
        hurst = RegimeDetector._hurst_exponent(df_1h['close'].tail(100))
        persistence = 'PERSISTENT' if hurst > 0.55 else 'MEAN_REVERTING' if hurst < 0.45 else 'RANDOM'

        # 4. VIX Proxy (using BTC realized volatility)
        rv_20 = RegimeDetector._realized_volatility(df_1h['close'], 20)
        fear_gauge = 'HIGH_FEAR' if rv_20 > 0.6 else 'LOW_FEAR'

        # Regime Classification Logic
        regime = 'RANGING'
        confidence = 0
        strategy_params = {}

        if adx_current > 30 and hurst > 0.55:
            # Trending Regime
            if df_1h['close'].iloc[-1] > df_1h['close'].rolling(20).mean().iloc[-1]:
                regime = 'TRENDING_BULL'
            else:
                regime = 'TRENDING_BEAR'
            confidence = min(95, adx_current * 2 + (hurst - 0.5) * 40)
            strategy_params = {'trend_following': True, 'max_positions': 3}

        elif volatility_regime == 'HIGH' or rv_20 > 0.8:
            regime = 'VOLATILE'
            confidence = min(90, rv_20 * 100)
            strategy_params = {'tight_stops': True, 'small_size': 0.5}

        else:
            # Ranging/Mean Reversion
            regime = 'RANGING'
            confidence = min(85, (1 - adx_current/100) * 80)
            strategy_params = {'oscillator_signals': True, 'range_bound': True}

        return {
            'regime': regime,
            'confidence': confidence,
            'trend_strength': trend_strength,
            'volatility_regime': volatility_regime,
            'hurst_exponent': hurst,
            'vix_proxy': rv_20,
            'strategy_params': strategy_params,
            'recommended_strategies': RegimeDetector._get_strategy_recommendations(regime)
        }

    @staticmethod
    def _hurst_exponent(prices: pd.Series, max_lag: int = 20) -> float:
        """Calculate Hurst Exponent for persistence analysis."""
        lags = range(2, max_lag)
        tau = [np.sqrt(np.std(np.subtract(prices[lag:], prices[:-lag]))) for lag in lags]
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        return poly[0] * 2.0

    @staticmethod
    def _realized_volatility(prices: pd.Series, window: int = 20) -> float:
        """20-period realized volatility (VIX proxy)."""
        returns = np.log(prices / prices.shift(1)).dropna()
        return returns.tail(window).std() * np.sqrt(365 * 24) * 100

    @staticmethod
    def _get_strategy_recommendations(regime: str) -> List[str]:
        recommendations = {
            'TRENDING_BULL': ['Trend Following', 'Breakout', 'Liquidity Trap Long'],
            'TRENDING_BEAR': ['Short Momentum', 'Breakdown', 'Liquidity Trap Short'],
            'RANGING': ['Mean Reversion', 'Range Fade', 'Scalping'],
            'VOLATILE': ['Vol Breakout', 'Tight Range', 'Wait & See']
        }
        return recommendations.get(regime, ['Conservative'])

# Usage Example:
# regime_info = RegimeDetector.detect_regime(df_daily, df_1h)
# if regime_info['regime'] == 'TRENDING_BULL':
#     use_trend_strategy = True