"""
Advanced Technical Indicators for Futures Trading
Includes: SMA, EMA, MACD, RSI, Doji Pattern Detection
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Advanced technical analysis indicators."""

    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
        """Calculate Simple Moving Average."""
        return df[column].rolling(window=period).mean()

    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
        """Calculate Exponential Moving Average."""
        return df[column].ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Returns:
            Dict with 'macd', 'signal', 'histogram'
        """
        close = df['close']

        # MACD Line
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow

        # Signal Line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()

        # Histogram
        histogram = macd_line - signal_line

        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
        """
        Calculate RSI (Relative Strength Index).

        Returns:
            RSI values (0-100)
        """
        close = df[column]
        delta = close.diff()

        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def detect_doji(df: pd.DataFrame, threshold: float = 0.1) -> pd.Series:
        """
        Detect Doji candlestick patterns.

        A Doji forms when open and close prices are very close (within threshold%).

        Args:
            df: DataFrame with OHLC data
            threshold: Maximum % difference between open/close (default 0.1%)

        Returns:
            Boolean series indicating Doji candles
        """
        body_size = abs(df['close'] - df['open'])
        candle_range = df['high'] - df['low']

        # Avoid division by zero
        candle_range = candle_range.replace(0, np.nan)

        body_pct = (body_size / candle_range) * 100

        # Doji if body is less than threshold% of total range
        is_doji = body_pct <= threshold

        return is_doji

    @staticmethod
    def detect_fractals(df: pd.DataFrame, window: int = 2) -> Dict[str, pd.Series]:
        """
        Detect Williams Fractals (Bullish/Bearish).
        """
        # Bearish Fractal (Resistance / High point)
        bearish_fractal = df['high'] == df['high'].rolling(window=2*window+1, center=True).max()
        # Bullish Fractal (Support / Low point)
        bullish_fractal = df['low'] == df['low'].rolling(window=2*window+1, center=True).min()
        
        return {
            'bearish': bearish_fractal.fillna(False),
            'bullish': bullish_fractal.fillna(False)
        }

    @staticmethod
    def detect_candlestick_patterns(df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Detect Advanced Candlestick Patterns: Engulfing, Hammer.
        """
        prev_close = df['close'].shift(1)
        prev_open = df['open'].shift(1)
        curr_close = df['close']
        curr_open = df['open']
        
        # Bullish Engulfing
        is_prev_bearish = prev_close < prev_open
        is_curr_bullish = curr_close > curr_open
        bullish_engulfing = is_prev_bearish & is_curr_bullish & (curr_open <= prev_close) & (curr_close >= prev_open)
        
        # Bearish Engulfing
        is_prev_bullish = prev_close > prev_open
        is_curr_bearish = curr_close < curr_open
        bearish_engulfing = is_prev_bullish & is_curr_bearish & (curr_open >= prev_close) & (curr_close <= prev_open)
        
        # Hammer (Bullish at bottom)
        body = abs(curr_close - curr_open)
        upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)
        lower_shadow = df[['open', 'close']].min(axis=1) - df['low']
        
        is_hammer = (lower_shadow > 2 * body) & (upper_shadow <= body * 0.5) & is_curr_bullish
        
        return {
            'bullish_engulfing': bullish_engulfing.fillna(False),
            'bearish_engulfing': bearish_engulfing.fillna(False),
            'hammer': is_hammer.fillna(False)
        }

    @staticmethod
    def calculate_fibonacci_levels(df: pd.DataFrame, lookback: int = 100) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels from recent high/low.
        """
        recent = df.tail(lookback)
        recent_max = recent['high'].max()
        recent_min = recent['low'].min()
        
        diff = recent_max - recent_min
        
        return {
            '0.0': recent_max,
            '0.236': recent_max - 0.236 * diff,
            '0.382': recent_max - 0.382 * diff,
            '0.5': recent_max - 0.5 * diff,
            '0.618': recent_max - 0.618 * diff,
            '1.0': recent_min
        }

    @staticmethod
    def detect_fvg(df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Detect Fair Value Gaps (FVG) / Imbalances (SMC).
        Bullish FVG: Low of candle 3 is higher than High of candle 1.
        Bearish FVG: High of candle 3 is lower than Low of candle 1.
        """
        high_prev = df['high'].shift(2)
        low_prev = df['low'].shift(2)
        
        # We also want the gap to be significant, but for now simple structure is enough
        bullish_fvg = df['low'] > high_prev
        bearish_fvg = df['high'] < low_prev
        
        return {
            'bullish_fvg': bullish_fvg.fillna(False),
            'bearish_fvg': bearish_fvg.fillna(False)
        }

    @staticmethod
    def detect_liquidity_sweeps(df: pd.DataFrame, window: int = 20) -> Dict[str, pd.Series]:
        """
        Detect Liquidity Sweeps (SMC).
        Bullish Sweep: Price sweeps previous significant low but closes above it.
        Bearish Sweep: Price sweeps previous significant high but closes below it.
        """
        prev_lows = df['low'].rolling(window=window).min().shift(1)
        prev_highs = df['high'].rolling(window=window).max().shift(1)
        
        bullish_sweep = (df['low'] < prev_lows) & (df['close'] > prev_lows)
        bearish_sweep = (df['high'] > prev_highs) & (df['close'] < prev_highs)
        
        return {
            'bullish_sweep': bullish_sweep.fillna(False),
            'bearish_sweep': bearish_sweep.fillna(False)
        }

    @staticmethod
    def get_trend_direction(df: pd.DataFrame, sma_period: int = 50, ema_period: int = 20) -> str:
        """
        Determine trend direction using SMA/EMA.

        Returns:
            'BULLISH', 'BEARISH', or 'NEUTRAL'
        """
        if len(df) < max(sma_period, ema_period):
            return 'NEUTRAL'

        sma = TechnicalIndicators.calculate_sma(df, sma_period)
        ema = TechnicalIndicators.calculate_ema(df, ema_period)
        current_price = df['close'].iloc[-1]

        sma_val = sma.iloc[-1]
        ema_val = ema.iloc[-1]

        # Strong uptrend: Price > EMA > SMA
        if current_price > ema_val > sma_val:
            return 'BULLISH'

        # Strong downtrend: Price < EMA < SMA
        elif current_price < ema_val < sma_val:
            return 'BEARISH'

        else:
            return 'NEUTRAL'

    @staticmethod
    def check_macd_crossover(macd_data: Dict[str, pd.Series], lookback: int = 3) -> Optional[str]:
        """
        Check for MACD crossover in recent candles.

        Args:
            macd_data: Dict from calculate_macd()
            lookback: Number of candles to check

        Returns:
            'BULLISH_CROSS' (MACD crosses above signal)
            'BEARISH_CROSS' (MACD crosses below signal)
            None (no crossover)
        """
        macd = macd_data['macd'].iloc[-lookback:]
        signal = macd_data['signal'].iloc[-lookback:]

        # Bullish crossover: MACD was below, now above signal
        if (macd.iloc[-2] < signal.iloc[-2]) and (macd.iloc[-1] > signal.iloc[-1]):
            return 'BULLISH_CROSS'

        # Bearish crossover: MACD was above, now below signal
        elif (macd.iloc[-2] > signal.iloc[-2]) and (macd.iloc[-1] < signal.iloc[-1]):
            return 'BEARISH_CROSS'

        return None

    @staticmethod
    def check_rsi_condition(rsi: pd.Series, overbought: float = 70, oversold: float = 30) -> Optional[str]:
        """
        Check RSI overbought/oversold conditions.

        Returns:
            'OVERBOUGHT' (RSI > 70)
            'OVERSOLD' (RSI < 30)
            None (neutral)
        """
        current_rsi = rsi.iloc[-1]

        if current_rsi > overbought:
            return 'OVERBOUGHT'
        elif current_rsi < oversold:
            return 'OVERSOLD'

        return None

    @staticmethod
    def calculate_liquidity_score(df: pd.DataFrame, volume_period: int = 20) -> float:
        """
        Calculate market liquidity score based on volume.

        Returns:
            Score 0-100 (higher = more liquid)
        """
        if len(df) < volume_period:
            return 50.0  # Default neutral

        avg_volume = df['volume'].rolling(window=volume_period).mean().iloc[-1]
        current_volume = df['volume'].iloc[-1]

        # Volume ratio
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        # Score: 50 is normal, >70 is high liquidity, <30 is low
        score = min(100, max(0, 50 + (volume_ratio - 1) * 50))

        return score

    @staticmethod
    def analyze_pullback(df: pd.DataFrame, lookback: int = 15) -> Dict:
        """
        Detect and analyze short-term pullbacks.

        Args:
            df: Recent price data
            lookback: Minutes to analyze (for 1m data)

        Returns:
            Dict with pullback info
        """
        if len(df) < lookback:
            return {'is_pullback': False, 'strength': 0}

        recent = df.tail(lookback)

        # Check if price is retracing
        high_price = recent['high'].max()
        current_price = recent['close'].iloc[-1]
        pullback_pct = ((high_price - current_price) / high_price) * 100

        # Pullback detected if price dropped >0.5% from recent high
        is_pullback = pullback_pct > 0.5

        # Strength: 0-100 (higher = stronger pullback)
        strength = min(100, pullback_pct * 20)

        return {
            'is_pullback': is_pullback,
            'strength': strength,
            'pullback_pct': pullback_pct,
            'high_price': high_price,
            'current_price': current_price
        }


class SignalGenerator:
    """Generate trading signals based on multiple indicators."""

    @staticmethod
    def generate_entry_signal(
        df_macro: pd.DataFrame,  # 1H/4H data
        df_micro: pd.DataFrame,  # 5m/15m data
        macro_timeframe: str = '1h',
        micro_timeframe: str = '5m'
    ) -> Dict:
        """
        Generate comprehensive entry signal.

        Returns:
            Dict with signal info
        """
        try:
            # 1. Macro Trend (1H/4H)
            macro_trend = TechnicalIndicators.get_trend_direction(df_macro, sma_period=50, ema_period=20)

            # 2. Micro Indicators (5m/15m)
            macd_data = TechnicalIndicators.calculate_macd(df_micro)
            rsi = TechnicalIndicators.calculate_rsi(df_micro)
            is_doji = TechnicalIndicators.detect_doji(df_micro)
            fractals = TechnicalIndicators.detect_fractals(df_micro)
            candle_patterns = TechnicalIndicators.detect_candlestick_patterns(df_micro)
            fib_levels = TechnicalIndicators.calculate_fibonacci_levels(df_macro)

            # SMC / ICT Advanced Concepts
            fvgs = TechnicalIndicators.detect_fvg(df_micro)
            sweeps = TechnicalIndicators.detect_liquidity_sweeps(df_micro)

            # 3. Check conditions
            macd_cross = TechnicalIndicators.check_macd_crossover(macd_data)
            rsi_condition = TechnicalIndicators.check_rsi_condition(rsi)
            latest_doji = is_doji.iloc[-1]

            # 4. Liquidity
            liquidity_score = TechnicalIndicators.calculate_liquidity_score(df_micro)

            # 5. Signal Logic
            signal = None
            strength = 0
            reasons = []

            # Advanced Pattern Checks
            latest_bullish_eng = True if candle_patterns['bullish_engulfing'].iloc[-1] else False
            latest_bearish_eng = True if candle_patterns['bearish_engulfing'].iloc[-1] else False
            latest_hammer = True if candle_patterns['hammer'].iloc[-1] else False
            
            # Check if recent candles formed a fractal support/resistance
            recent_bullish_fractal = True if fractals['bullish'].iloc[-4:-1].any() else False
            recent_bearish_fractal = True if fractals['bearish'].iloc[-4:-1].any() else False

            # SMC Structure Check
            recent_bullish_fvg = True if fvgs['bullish_fvg'].iloc[-3:-1].any() else False
            recent_bearish_fvg = True if fvgs['bearish_fvg'].iloc[-3:-1].any() else False

            recent_bullish_sweep = True if sweeps['bullish_sweep'].iloc[-3:-1].any() else False
            recent_bearish_sweep = True if sweeps['bearish_sweep'].iloc[-3:-1].any() else False

            # LONG Signal
            if macro_trend == 'BULLISH':
                score = 0
                if macd_cross == 'BULLISH_CROSS':
                    score += 30
                    reasons.append("MACD bullish crossover")
                if rsi_condition == 'OVERSOLD':
                    score += 20
                    reasons.append("RSI oversold")
                if latest_doji:
                    score += 15
                    reasons.append("Doji confirmation")
                if latest_bullish_eng:
                    score += 30
                    reasons.append("Bullish Engulfing pattern")
                if latest_hammer:
                    score += 20
                    reasons.append("Bullish Hammer pattern")
                if recent_bullish_fractal:
                    score += 25
                    reasons.append("Williams Bullish Fractal (Support)")
                if recent_bullish_fvg:
                    score += 35
                    reasons.append("SMC Bullish FVG (Imbalance Zone)")
                if recent_bullish_sweep:
                    score += 40
                    reasons.append("SMC Liquidity Sweep (Sell Stops Taken)")

                if score >= 60:
                    signal = 'LONG'
                    strength = min(100, score + (liquidity_score / 5))

            # SHORT Signal
            elif macro_trend == 'BEARISH':
                score = 0
                if macd_cross == 'BEARISH_CROSS':
                    score += 30
                    reasons.append("MACD bearish crossover")
                if rsi_condition == 'OVERBOUGHT':
                    score += 20
                    reasons.append("RSI overbought")
                if latest_doji:
                    score += 15
                    reasons.append("Doji confirmation")
                if latest_bearish_eng:
                    score += 30
                    reasons.append("Bearish Engulfing pattern")
                if recent_bearish_fractal:
                    score += 25
                    reasons.append("Williams Bearish Fractal (Resistance)")
                if recent_bearish_fvg:
                    score += 35
                    reasons.append("SMC Bearish FVG (Imbalance Zone)")
                if recent_bearish_sweep:
                    score += 40
                    reasons.append("SMC Liquidity Sweep (Buy Stops Taken)")

                if score >= 60:
                    signal = 'SHORT'
                    strength = min(100, score + (liquidity_score / 5))

            return {
                'signal': signal,
                'strength': strength,
                'macro_trend': macro_trend,
                'macd_cross': macd_cross,
                'rsi_condition': rsi_condition,
                'rsi_value': float(rsi.iloc[-1]),
                'doji_detected': bool(latest_doji),
                'bullish_engulfing': latest_bullish_eng,
                'bearish_engulfing': latest_bearish_eng,
                'hammer_detected': latest_hammer,
                'fibonacci_0_618': float(fib_levels.get('0.618', 0.0)),
                'bullish_fvg': recent_bullish_fvg,
                'bearish_fvg': recent_bearish_fvg,
                'bullish_sweep': recent_bullish_sweep,
                'bearish_sweep': recent_bearish_sweep,
                'liquidity_score': float(liquidity_score),
                'reasons': reasons,
                'timestamp': df_micro.index[-1] if hasattr(df_micro.index[-1], 'isoformat') else None
            }

        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return {
                'signal': None,
                'strength': 0,
                'error': str(e)
            }

    @staticmethod
    def calculate_dynamic_stop_loss(
        entry_price: float,
        signal_type: str,  # 'LONG' or 'SHORT'
        liquidity_score: float,
        indicator_strength: float,
        base_sl_pct: float = 2.0
    ) -> float:
        """
        Calculate dynamic stop loss based on market conditions.

        Args:
            entry_price: Entry price
            signal_type: 'LONG' or 'SHORT'
            liquidity_score: 0-100
            indicator_strength: 0-100
            base_sl_pct: Base SL percentage (default 2%)

        Returns:
            Stop loss price
        """
        # Adjust SL based on conditions
        sl_multiplier = 1.0

        # High liquidity + strong indicators = wider SL (more breathing room)
        if liquidity_score > 70 and indicator_strength > 80:
            sl_multiplier = 1.5  # 3% instead of 2%
        elif liquidity_score < 40 or indicator_strength < 60:
            sl_multiplier = 0.75  # 1.5% for weak signals

        sl_pct = base_sl_pct * sl_multiplier

        if signal_type == 'LONG':
            # SL below entry
            sl_price = entry_price * (1 - sl_pct / 100)
        else:  # SHORT
            # SL above entry
            sl_price = entry_price * (1 + sl_pct / 100)

        return sl_price

    @staticmethod
    def calculate_take_profit_targets(
        entry_price: float,
        stop_loss: float,
        signal_type: str,
        min_rrr: float = 2.0
    ) -> Dict[str, float]:
        """
        Calculate TP targets based on minimum Risk/Reward Ratio.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            signal_type: 'LONG' or 'SHORT'
            min_rrr: Minimum Risk/Reward Ratio (default 2.0)

        Returns:
            Dict with TP1, TP2, TP3
        """
        # Calculate risk
        risk = abs(entry_price - stop_loss)

        if signal_type == 'LONG':
            tp1 = entry_price + (risk * min_rrr)  # 1:2
            tp2 = entry_price + (risk * (min_rrr * 1.5))  # 1:3
            tp3 = entry_price + (risk * (min_rrr * 2))  # 1:4
        else:  # SHORT
            tp1 = entry_price - (risk * min_rrr)
            tp2 = entry_price - (risk * (min_rrr * 1.5))
            tp3 = entry_price - (risk * (min_rrr * 2))

        return {
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'risk': risk,
            'rrr': min_rrr
        }
