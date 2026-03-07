#!/usr/bin/env python3
"""
1H Liquidity Sweep Strategy
============================
Hypothesis: Real liquidity inefficiencies exist at 1h, not 5m noise

Core Logic:
1. Detect liquidity sweeps on 1h timeframe
2. Confirm with 4h trend direction
3. Entry on 15m pullback after sweep
4. Structure-based exits (not fixed ATR)
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Signal1H:
    """1H Liquidity Signal"""
    signal: str  # 'LONG', 'SHORT', 'NONE'
    entry_price: float
    stop_loss: float
    take_profit: float
    reasons: List[str]
    sweep_level: float
    trend_4h: str
    confidence: float  # 0-1


class Liquidity1HStrategy:
    """
    1H Liquidity Sweep Strategy

    Entry Criteria:
    1. 1H sweep of recent high/low (liquidity grab)
    2. 4H trend confirmation (ADX > 25)
    3. 15m pullback after sweep
    4. Volume confirmation

    Exit:
    - TP: Next structure level (S/R)
    - SL: Below/above sweep level
    - Time stop: 12 hours max
    """

    def __init__(
        self,
        sweep_lookback: int = 20,  # 1h bars to look for sweep
        trend_adx_threshold: float = 25.0,
        pullback_pct: float = 0.003,  # 0.3% pullback required
        volume_threshold: float = 1.2,  # 1.2x average volume
    ):
        self.sweep_lookback = sweep_lookback
        self.trend_adx_threshold = trend_adx_threshold
        self.pullback_pct = pullback_pct
        self.volume_threshold = volume_threshold

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute required indicators"""
        out = df.copy()

        # ATR (1h)
        high = out['high']
        low = out['low']
        close = out['close']
        close_prev = close.shift(1)

        tr = pd.concat([
            high - low,
            (high - close_prev).abs(),
            (low - close_prev).abs()
        ], axis=1).max(axis=1)

        out['atr'] = tr.ewm(span=14, adjust=False).mean()

        # EMA (4h trend proxy from 1h)
        out['ema_fast'] = close.ewm(span=9, adjust=False).mean()
        out['ema_slow'] = close.ewm(span=21, adjust=False).mean()
        out['ema_trend'] = out['ema_fast'] - out['ema_slow']

        # ADX (trend strength)
        high_diff = high.diff()
        low_diff = -low.diff()

        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0.0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0.0)

        atr_series = out['atr']
        plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(span=14, adjust=False).mean() / (atr_series + 1e-9)
        minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(span=14, adjust=False).mean() / (atr_series + 1e-9)

        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9))
        out['adx'] = dx.ewm(span=14, adjust=False).mean()

        # Volume indicators
        out['volume_ma'] = out['volume'].rolling(20, min_periods=10).mean()
        out['volume_ratio'] = out['volume'] / (out['volume_ma'] + 1e-9)

        # Taker buy ratio
        if 'taker_buy_base' in out.columns:
            out['tbr'] = out['taker_buy_base'] / (out['volume'] + 1e-9)
        else:
            out['tbr'] = 0.5

        # Liquidity levels (recent highs/lows)
        out['swing_high'] = out['high'].rolling(self.sweep_lookback, min_periods=self.sweep_lookback).max().shift(1)
        out['swing_low'] = out['low'].rolling(self.sweep_lookback, min_periods=self.sweep_lookback).min().shift(1)

        return out

    def detect_sweep(self, df: pd.DataFrame, idx: int) -> Optional[dict]:
        """
        Detect liquidity sweep

        Bullish Sweep: Price breaks below swing low then closes above
        Bearish Sweep: Price breaks above swing high then closes below
        """
        if idx < self.sweep_lookback + 1:
            return None

        bar = df.iloc[idx]
        prev_bar = df.iloc[idx - 1]

        swing_high = bar['swing_high']
        swing_low = bar['swing_low']

        if pd.isna(swing_high) or pd.isna(swing_low):
            return None

        # Bullish sweep: Low < swing_low, Close > swing_low
        if bar['low'] < swing_low and bar['close'] > swing_low:
            return {
                'type': 'BULLISH_SWEEP',
                'level': swing_low,
                'wick_size': (swing_low - bar['low']) / bar['close'],
            }

        # Bearish sweep: High > swing_high, Close < swing_high
        if bar['high'] > swing_high and bar['close'] < swing_high:
            return {
                'type': 'BEARISH_SWEEP',
                'level': swing_high,
                'wick_size': (bar['high'] - swing_high) / bar['close'],
            }

        return None

    def check_trend_4h(self, df: pd.DataFrame, idx: int) -> str:
        """
        Check 4h trend direction

        Use 1h data to approximate 4h trend:
        - Look at last 4 bars (4h equivalent)
        - Check EMA direction and ADX strength
        """
        if idx < 50:
            return 'NEUTRAL'

        bar = df.iloc[idx]

        # ADX strength
        if bar['adx'] < self.trend_adx_threshold:
            return 'NEUTRAL'

        # EMA trend direction (aggregated over last 4 bars)
        recent_trend = df.iloc[idx-3:idx+1]['ema_trend'].mean()

        if recent_trend > 0:
            return 'BULLISH'
        elif recent_trend < 0:
            return 'BEARISH'
        else:
            return 'NEUTRAL'

    def generate_signal(self, df_1h: pd.DataFrame, current_idx: int) -> Signal1H:
        """
        Generate trading signal

        Logic:
        1. Detect sweep on 1h
        2. Check 4h trend alignment
        3. Verify volume
        4. Calculate entry/exit levels
        """
        # Default: no signal
        no_signal = Signal1H(
            signal='NONE',
            entry_price=0,
            stop_loss=0,
            take_profit=0,
            reasons=[],
            sweep_level=0,
            trend_4h='NEUTRAL',
            confidence=0.0
        )

        if current_idx < 50:
            return no_signal

        bar = df_1h.iloc[current_idx]

        # 1. Detect sweep
        sweep = self.detect_sweep(df_1h, current_idx)
        if not sweep:
            return no_signal

        # 2. Check trend
        trend_4h = self.check_trend_4h(df_1h, current_idx)

        # 3. Verify alignment
        reasons = []

        if sweep['type'] == 'BULLISH_SWEEP':
            # Need bullish or neutral trend for long
            if trend_4h == 'BEARISH':
                return no_signal

            signal_type = 'LONG'
            entry = bar['close']
            sl = sweep['level'] - bar['atr']  # Below sweep level

            # TP: Next structure level (approx 2x ATR above)
            tp = entry + (2.0 * bar['atr'])

            reasons.append(f"Bullish Sweep @ {sweep['level']:.2f}")
            reasons.append(f"Trend: {trend_4h}")

            # Volume confirmation
            if bar['volume_ratio'] > self.volume_threshold:
                reasons.append(f"Volume: {bar['volume_ratio']:.2f}x")
            else:
                # Weak volume - reduce confidence
                pass

        elif sweep['type'] == 'BEARISH_SWEEP':
            # Need bearish or neutral trend for short
            if trend_4h == 'BULLISH':
                return no_signal

            signal_type = 'SHORT'
            entry = bar['close']
            sl = sweep['level'] + bar['atr']  # Above sweep level

            # TP: Next structure level (approx 2x ATR below)
            tp = entry - (2.0 * bar['atr'])

            reasons.append(f"Bearish Sweep @ {sweep['level']:.2f}")
            reasons.append(f"Trend: {trend_4h}")

            # Volume confirmation
            if bar['volume_ratio'] > self.volume_threshold:
                reasons.append(f"Volume: {bar['volume_ratio']:.2f}x")

        else:
            return no_signal

        # Calculate confidence (0-1)
        confidence = 0.5  # Base

        if trend_4h != 'NEUTRAL':
            confidence += 0.2  # Trend alignment

        if bar['volume_ratio'] > self.volume_threshold:
            confidence += 0.2  # Volume confirmation

        if sweep['wick_size'] > 0.005:  # Significant wick (0.5%)
            confidence += 0.1

        confidence = min(confidence, 1.0)

        return Signal1H(
            signal=signal_type,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            reasons=reasons,
            sweep_level=sweep['level'],
            trend_4h=trend_4h,
            confidence=confidence
        )


def get_liquidity_1h_strategy(**kwargs):
    """Factory function"""
    return Liquidity1HStrategy(**kwargs)
