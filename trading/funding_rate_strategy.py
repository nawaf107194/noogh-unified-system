#!/usr/bin/env python3
"""
Funding Rate Mean Reversion Strategy
=====================================
Hypothesis: Extreme funding rates mean-revert

Core Logic:
1. Detect extreme funding rate (> P90 or < P10)
2. Trade opposite direction (high funding → short)
3. Exit when funding normalizes or time stop
4. Based on economic force (funding payments) not price patterns

This is ARBITRAGE, not directional prediction.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class FundingRateSignal:
    """Funding Rate Signal"""
    signal: str  # 'LONG', 'SHORT', 'NONE'
    entry_price: float
    stop_loss: float
    take_profit: float
    reasons: List[str]
    funding_rate: float
    funding_percentile: float
    days_since_extreme: int


class FundingRateStrategy:
    """
    Funding Rate Mean Reversion Strategy

    Entry Criteria:
    1. Funding rate > P90 (extremely positive) → SHORT
    2. Funding rate < P10 (extremely negative) → LONG
    3. Confirm with price momentum (avoid catching falling knife)
    4. Position size based on funding extremity

    Exit:
    - TP: Funding rate returns to P25-P75 range
    - SL: 3% adverse move (wider than typical)
    - Time stop: 7 days max
    """

    def __init__(
        self,
        lookback_days: int = 90,  # Days for funding percentile
        entry_high_pct: float = 90.0,  # Enter short when funding > P90
        entry_low_pct: float = 10.0,   # Enter long when funding < P10
        exit_high_pct: float = 75.0,   # Exit when funding normalizes to < P75
        exit_low_pct: float = 25.0,    # Exit when funding normalizes to > P25
        max_hold_hours: int = 168,     # 7 days max hold
        stop_loss_pct: float = 3.0,    # 3% stop loss
    ):
        self.lookback_days = lookback_days
        self.entry_high_pct = entry_high_pct
        self.entry_low_pct = entry_low_pct
        self.exit_high_pct = exit_high_pct
        self.exit_low_pct = exit_low_pct
        self.max_hold_hours = max_hold_hours
        self.stop_loss_pct = stop_loss_pct

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute funding rate indicators

        Expects df with columns: timestamp, close, funding_rate
        funding_rate in decimal form (e.g., 0.0001 = 0.01%)
        """
        out = df.copy()

        # Funding rate percentile (rolling)
        out['funding_pct'] = out['funding_rate'].rolling(
            self.lookback_days * 3,  # 3 funding periods per day (8h each)
            min_periods=30
        ).apply(
            lambda x: (x.iloc[-1] >= x).sum() / len(x) * 100 if len(x) > 0 else 50
        )

        # Funding rate MA (for normalization detection)
        out['funding_ma'] = out['funding_rate'].rolling(30, min_periods=10).mean()

        # Price momentum (don't counter-trade strong trends)
        out['returns_24h'] = out['close'].pct_change(24)  # 24h return (assuming 1h bars)
        out['returns_7d'] = out['close'].pct_change(168)  # 7d return

        # Volatility (for stop loss adjustment)
        out['volatility'] = out['close'].pct_change().rolling(24).std() * np.sqrt(24)

        return out

    def detect_extreme_funding(self, df: pd.DataFrame, idx: int) -> Optional[dict]:
        """
        Detect extreme funding rate conditions

        Returns dict with:
        - type: 'HIGH_FUNDING' or 'LOW_FUNDING'
        - percentile: current funding percentile
        - rate: current funding rate
        """
        if idx < self.lookback_days * 3:
            return None

        bar = df.iloc[idx]

        if pd.isna(bar['funding_pct']) or pd.isna(bar['funding_rate']):
            return None

        # High funding (longs paying shorts) → opportunity to SHORT
        if bar['funding_pct'] >= self.entry_high_pct:
            return {
                'type': 'HIGH_FUNDING',
                'percentile': bar['funding_pct'],
                'rate': bar['funding_rate'],
            }

        # Low funding (shorts paying longs) → opportunity to LONG
        if bar['funding_pct'] <= self.entry_low_pct:
            return {
                'type': 'LOW_FUNDING',
                'percentile': bar['funding_pct'],
                'rate': bar['funding_rate'],
            }

        return None

    def check_momentum_confirmation(self, df: pd.DataFrame, idx: int, signal_type: str) -> bool:
        """
        Check if price momentum confirms the funding trade

        For SHORT (high funding): Don't short into strong uptrend (> +20% week)
        For LONG (low funding): Don't long into strong downtrend (< -20% week)
        """
        bar = df.iloc[idx]

        if pd.isna(bar['returns_7d']):
            return True  # No data, allow trade

        if signal_type == 'SHORT':
            # Don't short if massive rally (> +30% in 7d)
            if bar['returns_7d'] > 0.30:
                return False

        elif signal_type == 'LONG':
            # Don't long if massive dump (< -30% in 7d)
            if bar['returns_7d'] < -0.30:
                return False

        return True

    def generate_signal(self, df: pd.DataFrame, current_idx: int) -> FundingRateSignal:
        """
        Generate trading signal based on funding rate extremes

        Logic:
        1. Detect extreme funding rate
        2. Check momentum confirmation
        3. Calculate entry/exit based on mean reversion expectation
        """
        no_signal = FundingRateSignal(
            signal='NONE',
            entry_price=0,
            stop_loss=0,
            take_profit=0,
            reasons=[],
            funding_rate=0,
            funding_percentile=0,
            days_since_extreme=0
        )

        if current_idx < self.lookback_days * 3:
            return no_signal

        bar = df.iloc[current_idx]

        # 1. Detect extreme funding
        extreme = self.detect_extreme_funding(df, current_idx)
        if not extreme:
            return no_signal

        reasons = []
        entry = bar['close']

        if extreme['type'] == 'HIGH_FUNDING':
            # High funding → SHORT
            signal_type = 'SHORT'

            # Momentum check
            if not self.check_momentum_confirmation(df, current_idx, 'SHORT'):
                return no_signal

            reasons.append(f"Extreme High Funding: {extreme['rate']*100:.4f}% (P{extreme['percentile']:.0f})")
            reasons.append("Market: Longs paying shorts → expect unwind")

            # SL: Above entry (wider stop for funding plays)
            sl = entry * (1 + self.stop_loss_pct / 100)

            # TP: Expect price decline as funding normalizes
            # Conservative: 2% decline
            tp = entry * (1 - 0.02)

        elif extreme['type'] == 'LOW_FUNDING':
            # Low funding → LONG
            signal_type = 'LONG'

            # Momentum check
            if not self.check_momentum_confirmation(df, current_idx, 'LONG'):
                return no_signal

            reasons.append(f"Extreme Low Funding: {extreme['rate']*100:.4f}% (P{extreme['percentile']:.0f})")
            reasons.append("Market: Shorts paying longs → expect cover")

            # SL: Below entry
            sl = entry * (1 - self.stop_loss_pct / 100)

            # TP: Expect price rise
            tp = entry * (1 + 0.02)

        else:
            return no_signal

        # Add 7d momentum context
        if not pd.isna(bar['returns_7d']):
            reasons.append(f"7d Return: {bar['returns_7d']*100:.1f}%")

        return FundingRateSignal(
            signal=signal_type,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            reasons=reasons,
            funding_rate=extreme['rate'],
            funding_percentile=extreme['percentile'],
            days_since_extreme=0  # Will track in backtesting
        )


def get_funding_rate_strategy(**kwargs):
    """Factory function"""
    return FundingRateStrategy(**kwargs)
