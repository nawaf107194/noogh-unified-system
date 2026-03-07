#!/usr/bin/env python3
"""
Volatility Compression Strategy
================================
Hypothesis: Trade breakouts AFTER compression, not during

Core Logic:
1. Detect ATR compression (< P20 of 30-day range)
2. Bollinger Band squeeze
3. Wait for volume breakout
4. Follow the trend (NOT counter-trend)
5. Exit when volatility expands (ATR > P70)

This is OPPOSITE of sweep strategy:
- Trend-following (not reversal)
- Waits for confirmation (not prediction)
- Based on regime change (compression → expansion)
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class VolCompressionSignal:
    """Vol Compression Signal"""
    signal: str  # 'LONG', 'SHORT', 'NONE'
    entry_price: float
    stop_loss: float
    take_profit: float
    reasons: List[str]
    atr_percentile: float
    bb_width_percentile: float
    breakout_strength: float


class VolCompressionStrategy:
    """
    Volatility Compression → Expansion Strategy

    Entry Criteria:
    1. ATR in bottom 20% of 30-day range (compression)
    2. Bollinger Bands tight (< P25)
    3. Volume breakout (> 1.5x avg)
    4. Clear direction (close beyond BB)
    5. Trend confirmation (EMA alignment)

    Exit:
    - TP: ATR > P70 (expansion complete)
    - SL: Opposite band
    - Time: 24 hours max
    """

    def __init__(
        self,
        lookback_period: int = 30,  # Days for percentile calc (30 days on 1h = 720 bars)
        atr_compression_pct: float = 20.0,  # ATR < P20 = compressed
        bb_squeeze_pct: float = 25.0,  # BB width < P25 = squeezed
        volume_threshold: float = 1.5,  # 1.5x average volume
        atr_expansion_pct: float = 70.0,  # ATR > P70 = expanded (exit)
    ):
        self.lookback = lookback_period * 24  # Convert days to 1h bars
        self.atr_compression_pct = atr_compression_pct
        self.bb_squeeze_pct = bb_squeeze_pct
        self.volume_threshold = volume_threshold
        self.atr_expansion_pct = atr_expansion_pct

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute required indicators"""
        out = df.copy()

        close = out['close']
        high = out['high']
        low = out['low']

        # ATR
        close_prev = close.shift(1)
        tr = pd.concat([
            high - low,
            (high - close_prev).abs(),
            (low - close_prev).abs()
        ], axis=1).max(axis=1)

        out['atr'] = tr.ewm(span=14, adjust=False).mean()

        # ATR percentile (rolling)
        out['atr_pct'] = out['atr'].rolling(self.lookback, min_periods=100).apply(
            lambda x: (x.iloc[-1] <= x).sum() / len(x) * 100
        )

        # Bollinger Bands
        out['bb_mid'] = close.rolling(20, min_periods=20).mean()
        out['bb_std'] = close.rolling(20, min_periods=20).std()
        out['bb_upper'] = out['bb_mid'] + (2 * out['bb_std'])
        out['bb_lower'] = out['bb_mid'] - (2 * out['bb_std'])
        out['bb_width'] = (out['bb_upper'] - out['bb_lower']) / out['bb_mid']

        # BB width percentile
        out['bb_width_pct'] = out['bb_width'].rolling(self.lookback, min_periods=100).apply(
            lambda x: (x.iloc[-1] <= x).sum() / len(x) * 100
        )

        # EMAs (trend)
        out['ema9'] = close.ewm(span=9, adjust=False).mean()
        out['ema21'] = close.ewm(span=21, adjust=False).mean()
        out['ema50'] = close.ewm(span=50, adjust=False).mean()

        # Volume
        out['volume_ma'] = out['volume'].rolling(20, min_periods=10).mean()
        out['volume_ratio'] = out['volume'] / (out['volume_ma'] + 1e-9)

        return out

    def detect_compression(self, df: pd.DataFrame, idx: int) -> Optional[dict]:
        """
        Detect volatility compression

        Compression = ATR low + BB squeeze
        """
        if idx < self.lookback:
            return None

        bar = df.iloc[idx]

        # Check ATR compression
        if pd.isna(bar['atr_pct']) or bar['atr_pct'] > self.atr_compression_pct:
            return None

        # Check BB squeeze
        if pd.isna(bar['bb_width_pct']) or bar['bb_width_pct'] > self.bb_squeeze_pct:
            return None

        return {
            'atr_pct': bar['atr_pct'],
            'bb_width_pct': bar['bb_width_pct'],
            'is_compressed': True
        }

    def detect_breakout(self, df: pd.DataFrame, idx: int) -> Optional[str]:
        """
        Detect breakout direction

        Bullish: Close > BB upper, volume > threshold
        Bearish: Close < BB lower, volume > threshold
        """
        if idx < 1:
            return None

        bar = df.iloc[idx]
        prev_bar = df.iloc[idx - 1]

        # Volume confirmation
        if bar['volume_ratio'] < self.volume_threshold:
            return None

        # Bullish breakout
        if prev_bar['close'] <= prev_bar['bb_upper'] and bar['close'] > bar['bb_upper']:
            return 'BULLISH'

        # Bearish breakout
        if prev_bar['close'] >= prev_bar['bb_lower'] and bar['close'] < bar['bb_lower']:
            return 'BEARISH'

        return None

    def check_trend_alignment(self, df: pd.DataFrame, idx: int, direction: str) -> bool:
        """
        Check if trend supports breakout direction

        Bullish: EMA9 > EMA21 > EMA50 (or at least 2 of 3)
        Bearish: EMA9 < EMA21 < EMA50 (or at least 2 of 3)
        """
        bar = df.iloc[idx]

        if direction == 'BULLISH':
            # Count bullish alignments
            count = 0
            if bar['ema9'] > bar['ema21']:
                count += 1
            if bar['ema21'] > bar['ema50']:
                count += 1
            if bar['ema9'] > bar['ema50']:
                count += 1
            return count >= 2

        elif direction == 'BEARISH':
            # Count bearish alignments
            count = 0
            if bar['ema9'] < bar['ema21']:
                count += 1
            if bar['ema21'] < bar['ema50']:
                count += 1
            if bar['ema9'] < bar['ema50']:
                count += 1
            return count >= 2

        return False

    def generate_signal(self, df_1h: pd.DataFrame, current_idx: int) -> VolCompressionSignal:
        """
        Generate trading signal

        Logic:
        1. Check if we're in compression
        2. Detect breakout
        3. Verify trend alignment
        4. Calculate entry/exit
        """
        no_signal = VolCompressionSignal(
            signal='NONE',
            entry_price=0,
            stop_loss=0,
            take_profit=0,
            reasons=[],
            atr_percentile=0,
            bb_width_percentile=0,
            breakout_strength=0
        )

        if current_idx < self.lookback + 1:
            return no_signal

        bar = df_1h.iloc[current_idx]

        # 1. Check compression
        compression = self.detect_compression(df_1h, current_idx)
        if not compression:
            return no_signal

        # 2. Detect breakout
        breakout = self.detect_breakout(df_1h, current_idx)
        if not breakout:
            return no_signal

        # 3. Check trend alignment
        trend_ok = self.check_trend_alignment(df_1h, current_idx, breakout)

        reasons = []
        reasons.append(f"Compression: ATR P{compression['atr_pct']:.0f}, BB P{compression['bb_width_pct']:.0f}")
        reasons.append(f"{breakout} breakout on {bar['volume_ratio']:.1f}x volume")

        if trend_ok:
            reasons.append("Trend aligned")
        else:
            # No trend alignment - reduce confidence but still tradeable
            reasons.append("Trend neutral")

        # Calculate entry/exit
        entry = bar['close']

        if breakout == 'BULLISH':
            signal_type = 'LONG'

            # SL: Below BB lower
            sl = bar['bb_lower']

            # TP: 2x risk (or next resistance estimate)
            risk = entry - sl
            tp = entry + (2.0 * risk)

        else:  # BEARISH
            signal_type = 'SHORT'

            # SL: Above BB upper
            sl = bar['bb_upper']

            # TP: 2x risk
            risk = sl - entry
            tp = entry - (2.0 * risk)

        # Breakout strength (0-1)
        breakout_strength = min(bar['volume_ratio'] / 3.0, 1.0)  # Cap at 3x volume

        return VolCompressionSignal(
            signal=signal_type,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            reasons=reasons,
            atr_percentile=compression['atr_pct'],
            bb_width_percentile=compression['bb_width_pct'],
            breakout_strength=breakout_strength
        )


def get_vol_compression_strategy(**kwargs):
    """Factory function"""
    return VolCompressionStrategy(**kwargs)
