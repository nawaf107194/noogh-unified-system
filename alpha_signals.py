#!/usr/bin/env python3
"""
NOOGH Alpha Signal Research Lab
=================================
Citadel-style signal discovery framework for crypto futures.

Discovers, tests, and ranks alpha signals across 20 categories.
Measures: Information Coefficient (IC), hit rate, decay, turnover.
Finds optimal signal combinations that survive transaction costs.

Usage:
    python3 alpha_signals.py --symbol BTCUSDT --days 90
    python3 alpha_signals.py --symbol ETHUSDT --days 180 --top 10
"""

import sys
import json
import time
import argparse
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Callable
from pathlib import Path

import numpy as np
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')

# ═══════════════════════════════════════════════════════════════
# Section 1: Data Layer
# ═══════════════════════════════════════════════════════════════

class DataFetcher:
    """Fetch historical klines from Binance."""
    BASE = "https://api.binance.com/api/v3"
    
    def fetch(self, symbol: str, interval: str = '1h', days: int = 90) -> np.ndarray:
        """Returns structured numpy array with OHLCV data."""
        start_ms = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        end_ms = int(datetime.now().timestamp() * 1000)
        all_data = []
        current = start_ms
        
        logger.info(f"📊 Downloading {symbol} {interval} ({days} days)...")
        while current < end_ms:
            resp = requests.get(f"{self.BASE}/klines", params={
                'symbol': symbol, 'interval': interval,
                'startTime': current, 'endTime': end_ms, 'limit': 1000
            }, timeout=10)
            if resp.status_code != 200: break
            data = resp.json()
            if not data: break
            for k in data:
                all_data.append((k[0], float(k[1]), float(k[2]), float(k[3]),
                                 float(k[4]), float(k[5]), int(k[8]),
                                 float(k[9]), float(k[10])))
            current = data[-1][6] + 1
            time.sleep(0.1)
        
        logger.info(f"✅ {len(all_data)} candles downloaded")
        
        dt = np.dtype([
            ('timestamp', 'i8'), ('open', 'f8'), ('high', 'f8'), ('low', 'f8'),
            ('close', 'f8'), ('volume', 'f8'), ('trades', 'i4'),
            ('taker_buy_vol', 'f8'), ('taker_buy_quote', 'f8')
        ])
        return np.array(all_data, dtype=dt)


# ═══════════════════════════════════════════════════════════════
# Section 2: Signal Definitions — 20 Alpha Signal Categories
# ═══════════════════════════════════════════════════════════════

class AlphaSignals:
    """
    20 categories of alpha signals for crypto futures.
    Each signal returns np.ndarray of same length as input,
    with values in range [-1, +1] (bearish to bullish).
    NaN = no signal (warmup period).
    """
    
    # ── Category 1: Momentum ──
    
    @staticmethod
    def sig_rsi_mean_reversion(close: np.ndarray, period: int = 14) -> np.ndarray:
        """RSI mean reversion: oversold → buy, overbought → sell."""
        rsi = _rsi(close, period)
        # Normalize: 30 → +1 (buy), 70 → -1 (sell), 50 → 0
        signal = np.where(rsi < 50, (50 - rsi) / 20, (50 - rsi) / 20)
        return np.clip(signal, -1, 1)
    
    @staticmethod
    def sig_rsi_momentum(close: np.ndarray, period: int = 14) -> np.ndarray:
        """RSI momentum: above 50 → bullish trending, below → bearish."""
        rsi = _rsi(close, period)
        return np.clip((rsi - 50) / 50, -1, 1)
    
    @staticmethod
    def sig_macd_crossover(close: np.ndarray) -> np.ndarray:
        """MACD histogram sign as trend signal."""
        ema12 = _ema(close, 12)
        ema26 = _ema(close, 26)
        macd = ema12 - ema26
        signal = _ema(macd, 9)
        hist = macd - signal
        # Normalize by ATR
        atr = _atr(close, close, close, 14)  # simplified
        atr = np.where(atr == 0, 1, atr)
        return np.clip(hist / atr, -1, 1)
    
    @staticmethod
    def sig_price_momentum(close: np.ndarray, lookback: int = 10) -> np.ndarray:
        """Simple price momentum: % change over lookback period."""
        ret = np.full_like(close, np.nan)
        for i in range(lookback, len(close)):
            ret[i] = (close[i] - close[i - lookback]) / close[i - lookback]
        return np.clip(ret * 10, -1, 1)  # Scale: ±10% → ±1
    
    # ── Category 2: Mean Reversion ──
    
    @staticmethod
    def sig_bollinger_squeeze(close: np.ndarray, period: int = 20) -> np.ndarray:
        """Bollinger band position: below lower → buy, above upper → sell."""
        signal = np.full_like(close, np.nan)
        for i in range(period - 1, len(close)):
            w = close[i - period + 1:i + 1]
            m, s = np.mean(w), np.std(w)
            if s > 0:
                z = (close[i] - m) / (2 * s)
                signal[i] = -np.clip(z, -1, 1)  # Inverted: below band = buy
        return signal
    
    @staticmethod
    def sig_distance_from_vwap(close: np.ndarray, volume: np.ndarray, period: int = 20) -> np.ndarray:
        """Distance from VWAP as mean-reversion signal."""
        signal = np.full_like(close, np.nan)
        for i in range(period - 1, len(close)):
            v = volume[i - period + 1:i + 1]
            c = close[i - period + 1:i + 1]
            total_vol = np.sum(v)
            if total_vol > 0:
                vwap = np.sum(c * v) / total_vol
                dist = (close[i] - vwap) / vwap
                signal[i] = -np.clip(dist * 50, -1, 1)  # Mean revert
        return signal
    
    # ── Category 3: Volatility ──
    
    @staticmethod
    def sig_atr_breakout(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """ATR expansion = breakout imminent. Direction from price vs SMA."""
        atr = _atr(high, low, close, period)
        sma = _sma(close, period)
        atr_sma = _sma(atr, period)
        
        signal = np.full_like(close, np.nan)
        for i in range(period * 2, len(close)):
            if atr_sma[i] > 0:
                expansion = atr[i] / atr_sma[i] - 1
                direction = 1.0 if close[i] > sma[i] else -1.0
                signal[i] = direction * np.clip(expansion, 0, 1)
        return signal
    
    @staticmethod
    def sig_volatility_contraction(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        """Bollinger bandwidth contraction → imminent move. Direction from EMA."""
        signal = np.full_like(close, np.nan)
        ema9 = _ema(close, 9)
        ema21 = _ema(close, 21)
        for i in range(20, len(close)):
            w = close[i - 19:i + 1]
            bw = (np.max(w) - np.min(w)) / np.mean(w)
            bw_prev = (np.max(close[i-39:i-19]) - np.min(close[i-39:i-19])) / np.mean(close[i-39:i-19]) if i >= 40 else bw
            contraction = 1 - bw / max(bw_prev, 0.001)
            direction = 1.0 if ema9[i] > ema21[i] else -1.0
            if contraction > 0.3:
                signal[i] = direction * np.clip(contraction, 0, 1)
            else:
                signal[i] = 0
        return signal
    
    # ── Category 4: Volume ──
    
    @staticmethod
    def sig_volume_spike(close: np.ndarray, volume: np.ndarray, period: int = 20) -> np.ndarray:
        """Volume spike with price direction confirmation."""
        signal = np.full_like(close, np.nan)
        for i in range(period, len(close)):
            avg_vol = np.mean(volume[i - period:i])
            if avg_vol > 0:
                vol_ratio = volume[i] / avg_vol
                price_dir = 1.0 if close[i] > close[i-1] else -1.0
                if vol_ratio > 2.0:
                    signal[i] = price_dir * np.clip((vol_ratio - 1) / 3, 0, 1)
                else:
                    signal[i] = 0
        return signal
    
    @staticmethod
    def sig_obv_trend(close: np.ndarray, volume: np.ndarray, period: int = 20) -> np.ndarray:
        """On-Balance Volume trend as confirmation signal."""
        obv = np.zeros_like(close)
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv[i] = obv[i-1] + volume[i]
            elif close[i] < close[i-1]:
                obv[i] = obv[i-1] - volume[i]
            else:
                obv[i] = obv[i-1]
        
        obv_sma = _sma(obv, period)
        signal = np.full_like(close, np.nan)
        for i in range(period, len(close)):
            if obv_sma[i] != 0:
                signal[i] = np.clip((obv[i] - obv_sma[i]) / abs(obv_sma[i]) * 5, -1, 1)
        return signal
    
    # ── Category 5: Microstructure ──
    
    @staticmethod
    def sig_taker_buy_ratio(taker_buy_vol: np.ndarray, volume: np.ndarray, period: int = 10) -> np.ndarray:
        """Taker buy ratio: >0.5 = aggressive buying, <0.5 = aggressive selling."""
        signal = np.full_like(volume, np.nan)
        for i in range(period, len(volume)):
            total = np.sum(volume[i - period:i + 1])
            buy = np.sum(taker_buy_vol[i - period:i + 1])
            if total > 0:
                ratio = buy / total
                signal[i] = np.clip((ratio - 0.5) * 4, -1, 1)  # 0.5 → 0, 0.75 → +1
        return signal
    
    @staticmethod
    def sig_trade_intensity(trades: np.ndarray, period: int = 20) -> np.ndarray:
        """Trade count relative to average — high intensity = momentum."""
        signal = np.full(len(trades), np.nan, dtype='f8')
        for i in range(period, len(trades)):
            avg = np.mean(trades[i - period:i])
            if avg > 0:
                intensity = trades[i] / avg - 1
                signal[i] = np.clip(intensity, -1, 1)
        return signal
    
    # ── Category 6: Trend Structure ──
    
    @staticmethod
    def sig_ema_cascade(close: np.ndarray) -> np.ndarray:
        """EMA cascade alignment: 9 > 21 > 50 = bullish, reverse = bearish."""
        ema9 = _ema(close, 9)
        ema21 = _ema(close, 21)
        ema50 = _ema(close, 50)
        
        signal = np.full_like(close, np.nan)
        for i in range(50, len(close)):
            if np.isnan(ema9[i]) or np.isnan(ema21[i]) or np.isnan(ema50[i]):
                continue
            bull = (ema9[i] > ema21[i]) + (ema21[i] > ema50[i]) + (ema9[i] > ema50[i])
            bear = (ema9[i] < ema21[i]) + (ema21[i] < ema50[i]) + (ema9[i] < ema50[i])
            signal[i] = (bull - bear) / 3
        return signal
    
    @staticmethod
    def sig_higher_highs(high: np.ndarray, low: np.ndarray, window: int = 5) -> np.ndarray:
        """Higher highs + higher lows = bullish structure."""
        signal = np.full_like(high, np.nan)
        for i in range(window * 4, len(high)):
            # Find last 4 swing points
            recent_highs = [np.max(high[i-j*window-window:i-j*window+1]) for j in range(4)]
            recent_lows = [np.min(low[i-j*window-window:i-j*window+1]) for j in range(4)]
            
            hh = sum(1 for j in range(1, len(recent_highs)) if recent_highs[j-1] > recent_highs[j])
            hl = sum(1 for j in range(1, len(recent_lows)) if recent_lows[j-1] > recent_lows[j])
            lh = sum(1 for j in range(1, len(recent_highs)) if recent_highs[j-1] < recent_highs[j])
            ll = sum(1 for j in range(1, len(recent_lows)) if recent_lows[j-1] < recent_lows[j])
            
            bull_score = (hh + hl) / 6
            bear_score = (lh + ll) / 6
            signal[i] = bull_score - bear_score
        return np.clip(signal, -1, 1)
    
    # ── Category 7: Price Action ──
    
    @staticmethod
    def sig_candle_body_ratio(open_: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        """Large body candles = conviction. Direction from close vs open."""
        signal = np.full_like(close, np.nan)
        for i in range(1, len(close)):
            full_range = high[i] - low[i]
            if full_range > 0:
                body = abs(close[i] - open_[i])
                ratio = body / full_range
                direction = 1.0 if close[i] > open_[i] else -1.0
                signal[i] = direction * ratio if ratio > 0.6 else 0
        return signal
    
    @staticmethod
    def sig_gap_fill(open_: np.ndarray, close: np.ndarray) -> np.ndarray:
        """Gap between close[i-1] and open[i] tends to fill → mean reversion."""
        signal = np.full_like(close, np.nan)
        for i in range(1, len(close)):
            if close[i-1] > 0:
                gap = (open_[i] - close[i-1]) / close[i-1]
                signal[i] = -np.clip(gap * 50, -1, 1)  # Fade the gap
        return signal
    
    # ── Category 8: Multi-Timeframe ──
    
    @staticmethod
    def sig_multi_tf_momentum(close: np.ndarray) -> np.ndarray:
        """Align short/medium/long momentum: 5bar + 20bar + 50bar."""
        signal = np.full_like(close, np.nan)
        for i in range(50, len(close)):
            ret5 = (close[i] - close[i-5]) / close[i-5]
            ret20 = (close[i] - close[i-20]) / close[i-20]
            ret50 = (close[i] - close[i-50]) / close[i-50]
            
            s5 = np.clip(ret5 * 20, -1, 1)
            s20 = np.clip(ret20 * 10, -1, 1)
            s50 = np.clip(ret50 * 5, -1, 1)
            
            # All 3 agree = strong, disagree = weak
            signal[i] = 0.5 * s5 + 0.3 * s20 + 0.2 * s50
        return np.clip(signal, -1, 1)
    
    # ── Category 9: Regime ──
    
    @staticmethod
    def sig_regime_filter(close: np.ndarray, high: np.ndarray, low: np.ndarray) -> np.ndarray:
        """Identify trending (+1) vs ranging (0) vs volatile (-1) regimes."""
        atr = _atr(high, low, close, 14)
        ema = _ema(close, 20)
        signal = np.full_like(close, np.nan)
        
        for i in range(50, len(close)):
            # Trend strength: price distance from EMA
            trend = abs(close[i] - ema[i]) / ema[i] if ema[i] > 0 else 0
            # Volatility: ATR relative to price
            vol = atr[i] / close[i] if close[i] > 0 else 0
            
            if trend > 0.02 and vol < 0.03:
                signal[i] = 1.0  # Trending
            elif vol > 0.04:
                signal[i] = -1.0  # Volatile/chaotic
            else:
                signal[i] = 0.0  # Ranging
        return signal
    
    # ── Category 10: Composite ──
    
    @staticmethod
    def sig_z_score(close: np.ndarray, period: int = 20) -> np.ndarray:
        """Z-score of price relative to rolling distribution."""
        signal = np.full_like(close, np.nan)
        for i in range(period, len(close)):
            w = close[i - period:i]
            m, s = np.mean(w), np.std(w)
            if s > 0:
                z = (close[i] - m) / s
                signal[i] = -np.clip(z / 2, -1, 1)  # Mean reversion
        return signal


# ═══════════════════════════════════════════════════════════════
# Section 3: Helper Functions (numpy, no lookahead)
# ═══════════════════════════════════════════════════════════════

def _ema(data: np.ndarray, period: int) -> np.ndarray:
    result = np.full_like(data, np.nan, dtype='f8')
    if len(data) < period: return result
    result[period-1] = np.mean(data[:period])
    m = 2 / (period + 1)
    for i in range(period, len(data)):
        result[i] = (data[i] - result[i-1]) * m + result[i-1]
    return result

def _sma(data: np.ndarray, period: int) -> np.ndarray:
    result = np.full_like(data, np.nan, dtype='f8')
    for i in range(period-1, len(data)):
        result[i] = np.mean(data[i-period+1:i+1])
    return result

def _rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
    result = np.full_like(data, np.nan, dtype='f8')
    if len(data) < period + 1: return result
    deltas = np.diff(data)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    ag = np.mean(gains[:period])
    al = np.mean(losses[:period])
    for i in range(period, len(deltas)):
        ag = (ag * (period-1) + gains[i]) / period
        al = (al * (period-1) + losses[i]) / period
        result[i+1] = 100 - 100/(1 + ag/al) if al > 0 else 100
    return result

def _atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    result = np.full_like(close, np.nan, dtype='f8')
    if len(close) < period + 1: return result
    tr = np.maximum(high[1:]-low[1:], np.maximum(np.abs(high[1:]-close[:-1]), np.abs(low[1:]-close[:-1])))
    result[period] = np.mean(tr[:period])
    for i in range(period, len(tr)):
        result[i+1] = (result[i] * (period-1) + tr[i]) / period
    return result


# ═══════════════════════════════════════════════════════════════
# Section 4: Signal Testing Engine
# ═══════════════════════════════════════════════════════════════

@dataclass
class SignalTestResult:
    name: str
    ic: float              # Information Coefficient (correlation with forward returns)
    ic_t_stat: float       # T-stat of IC
    hit_rate: float        # % of correct direction predictions
    avg_return_long: float # Avg return when signal is positive
    avg_return_short: float # Avg return when signal is negative
    long_short_spread: float # Return spread between long and short quintiles
    decay_half_life: int   # Bars until signal strength halves
    turnover: float        # % of bars where signal changes direction
    sharpe: float          # Risk-adjusted return
    total_signals: int     # Number of non-NaN signals


class SignalTester:
    """Test individual signals for alpha content."""
    
    def __init__(self, forward_bars: int = 5):
        """
        Args:
            forward_bars: How many bars forward to measure return
        """
        self.forward_bars = forward_bars
    
    def test_signal(self, name: str, signal: np.ndarray, close: np.ndarray) -> SignalTestResult:
        """Test a single signal for predictive power."""
        
        # Forward returns (what we're trying to predict)
        fwd_returns = np.full_like(close, np.nan)
        for i in range(len(close) - self.forward_bars):
            fwd_returns[i] = (close[i + self.forward_bars] - close[i]) / close[i]
        
        # Align: both signal and fwd_returns must be non-NaN
        valid = ~np.isnan(signal) & ~np.isnan(fwd_returns) & (signal != 0)
        if np.sum(valid) < 30:
            return SignalTestResult(name, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        sig_v = signal[valid]
        ret_v = fwd_returns[valid]
        
        # 1. Information Coefficient (rank correlation)
        from scipy.stats import spearmanr
        try:
            ic, ic_p = spearmanr(sig_v, ret_v)
        except Exception:
            ic, ic_p = 0, 1
        
        ic_t = ic * np.sqrt(len(sig_v) - 2) / np.sqrt(1 - ic**2) if abs(ic) < 1 else 0
        
        # 2. Hit Rate
        correct = np.sum((sig_v > 0) & (ret_v > 0)) + np.sum((sig_v < 0) & (ret_v < 0))
        hit_rate = correct / len(sig_v) * 100
        
        # 3. Long/Short returns
        long_mask = sig_v > 0
        short_mask = sig_v < 0
        avg_long = np.mean(ret_v[long_mask]) * 100 if np.sum(long_mask) > 0 else 0
        avg_short = np.mean(ret_v[short_mask]) * 100 if np.sum(short_mask) > 0 else 0
        spread = avg_long - avg_short
        
        # 4. Decay analysis
        decay_hl = self._compute_decay(signal, close)
        
        # 5. Turnover
        direction_changes = np.sum(np.diff(np.sign(sig_v)) != 0)
        turnover = direction_changes / len(sig_v) * 100
        
        # 6. Sharpe
        trade_rets = np.where(sig_v > 0, ret_v, -ret_v)
        sharpe = np.mean(trade_rets) / np.std(trade_rets) * np.sqrt(252 * 24) if np.std(trade_rets) > 0 else 0
        
        return SignalTestResult(
            name=name, ic=round(ic, 4), ic_t_stat=round(ic_t, 2),
            hit_rate=round(hit_rate, 1),
            avg_return_long=round(avg_long, 4),
            avg_return_short=round(avg_short, 4),
            long_short_spread=round(spread, 4),
            decay_half_life=decay_hl,
            turnover=round(turnover, 1),
            sharpe=round(sharpe, 2),
            total_signals=int(np.sum(valid))
        )
    
    def _compute_decay(self, signal: np.ndarray, close: np.ndarray) -> int:
        """Measure how many bars until signal's IC halves."""
        valid = ~np.isnan(signal) & (signal != 0)
        sig = signal[valid]
        cl = close[:len(signal)]  # Align
        
        if len(sig) < 50:
            return 0
        
        from scipy.stats import spearmanr
        ics = []
        for lag in range(1, min(50, len(close) - np.sum(valid))):
            fwd = np.full(np.sum(valid), np.nan)
            valid_idx = np.where(valid)[0]
            for j, idx in enumerate(valid_idx):
                if idx + lag < len(close):
                    fwd[j] = (close[idx + lag] - close[idx]) / close[idx]
            
            fwd_valid = ~np.isnan(fwd)
            if np.sum(fwd_valid) > 20:
                try:
                    ic_lag, _ = spearmanr(sig[fwd_valid], fwd[fwd_valid])
                    ics.append(abs(ic_lag))
                except:
                    ics.append(0)
            else:
                ics.append(0)
        
        if not ics or ics[0] == 0:
            return 0
        
        half = ics[0] / 2
        for lag, ic in enumerate(ics):
            if ic < half:
                return lag + 1
        return len(ics)


# ═══════════════════════════════════════════════════════════════
# Section 5: Signal Combination & Ranking
# ═══════════════════════════════════════════════════════════════

class SignalCombiner:
    """Combine multiple weak signals into one strong composite."""
    
    @staticmethod
    def rank_signals(results: List[SignalTestResult]) -> List[SignalTestResult]:
        """Rank signals by composite quality score."""
        for r in results:
            r._quality_score = (
                abs(r.ic) * 40 +          # IC is king
                (r.hit_rate - 50) * 0.5 +  # Hit rate above 50%
                r.sharpe * 2 +              # Risk-adjusted
                r.long_short_spread * 5 -   # L/S spread
                r.turnover * 0.1            # Penalize high turnover
            )
        return sorted(results, key=lambda r: r._quality_score, reverse=True)
    
    @staticmethod
    def build_composite(signals: Dict[str, np.ndarray], weights: Dict[str, float]) -> np.ndarray:
        """Weighted combination of top signals."""
        n = max(len(s) for s in signals.values())
        composite = np.zeros(n)
        total_weight = 0
        
        for name, sig in signals.items():
            w = weights.get(name, 0)
            if w == 0:
                continue
            for i in range(len(sig)):
                if not np.isnan(sig[i]):
                    composite[i] += sig[i] * w
                    total_weight += w
        
        if total_weight > 0:
            composite /= (total_weight / len(signals))
        
        return np.clip(composite, -1, 1)
    
    @staticmethod
    def correlation_matrix(signals: Dict[str, np.ndarray]) -> Dict[str, Dict[str, float]]:
        """Check inter-signal correlations to avoid redundancy."""
        names = list(signals.keys())
        matrix = {}
        
        for i, n1 in enumerate(names):
            matrix[n1] = {}
            for j, n2 in enumerate(names):
                s1, s2 = signals[n1], signals[n2]
                valid = ~np.isnan(s1) & ~np.isnan(s2)
                if np.sum(valid) > 30:
                    corr = np.corrcoef(s1[valid], s2[valid])[0, 1]
                    matrix[n1][n2] = round(corr, 3)
                else:
                    matrix[n1][n2] = 0
        
        return matrix


# ═══════════════════════════════════════════════════════════════
# Section 6: Report Generator
# ═══════════════════════════════════════════════════════════════

def generate_report(results: List[SignalTestResult], symbol: str, days: int,
                    top_n: int = 10):
    """Print Citadel-style signal research report."""
    
    print("\n" + "=" * 80)
    print(f"  NOOGH ALPHA SIGNAL RESEARCH REPORT — {symbol}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')} | {days} days | {len(results)} signals tested")
    print("=" * 80)
    
    # Rank signals
    ranked = SignalCombiner.rank_signals(results)
    
    print(f"\n{'Rank':<5} {'Signal':<30} {'IC':<8} {'IC_t':<8} {'HR%':<8} {'Sharpe':<8} {'L/S':<10} {'Decay':<8} {'Turn%':<8} {'N':<6}")
    print("-" * 107)
    
    for i, r in enumerate(ranked[:top_n]):
        # Color coding
        ic_marker = "✅" if abs(r.ic) > 0.03 else "⚠️" if abs(r.ic) > 0.01 else "❌"
        
        print(f"{i+1:<5} {r.name:<30} {r.ic:+.4f}  {r.ic_t_stat:>6.1f}  {r.hit_rate:>5.1f}  {r.sharpe:>6.1f}  {r.long_short_spread:>8.4f}  {r.decay_half_life:>5}  {r.turnover:>6.1f}  {r.total_signals:>5} {ic_marker}")
    
    # Top signals analysis
    top_signals = ranked[:5]
    print(f"\n{'─' * 80}")
    print(f"  TOP 5 SIGNALS ANALYSIS")
    print(f"{'─' * 80}")
    
    for r in top_signals:
        print(f"\n  📊 {r.name}")
        print(f"     IC: {r.ic:+.4f} (t={r.ic_t_stat:.1f}) | Hit Rate: {r.hit_rate:.1f}%")
        print(f"     Long avg: {r.avg_return_long:+.4f}% | Short avg: {r.avg_return_short:+.4f}%")
        print(f"     Decay half-life: {r.decay_half_life} bars | Turnover: {r.turnover:.1f}%")
        
        verdict = "🟢 ALPHA" if abs(r.ic) > 0.03 and r.hit_rate > 52 else "🟡 WEAK" if abs(r.ic) > 0.01 else "🔴 NOISE"
        print(f"     Verdict: {verdict}")
    
    # Recommendations
    alpha_signals = [r for r in ranked if abs(r.ic) > 0.02 and r.hit_rate > 50]
    print(f"\n{'─' * 80}")
    print(f"  RECOMMENDATIONS")
    print(f"{'─' * 80}")
    
    if alpha_signals:
        print(f"\n  ✅ {len(alpha_signals)} signals show potential alpha:")
        for r in alpha_signals[:5]:
            print(f"     • {r.name} (IC={r.ic:+.4f}, HR={r.hit_rate:.1f}%)")
        
        print(f"\n  Suggested composite weights:")
        total_ic = sum(abs(r.ic) for r in alpha_signals[:5])
        for r in alpha_signals[:5]:
            w = abs(r.ic) / total_ic * 100
            print(f"     {r.name}: {w:.1f}%")
    else:
        print(f"\n  ⚠️ No signals with IC > 0.02 and HR > 50% found.")
        print(f"  Consider: longer holding periods, different symbols, or new data sources.")
    
    print("\n" + "=" * 80)


# ═══════════════════════════════════════════════════════════════
# Section 7: Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='NOOGH Alpha Signal Research Lab')
    parser.add_argument('--symbol', default='BTCUSDT', help='Trading pair')
    parser.add_argument('--interval', default='1h', help='Candle interval')
    parser.add_argument('--days', type=int, default=90, help='Days of history')
    parser.add_argument('--forward', type=int, default=5, help='Forward return bars')
    parser.add_argument('--top', type=int, default=15, help='Top N signals to show')
    parser.add_argument('--save', help='Save results to JSON')
    args = parser.parse_args()
    
    # 1. Download data
    fetcher = DataFetcher()
    data = fetcher.fetch(args.symbol, args.interval, args.days)
    
    if len(data) < 100:
        logger.error("❌ Insufficient data")
        return
    
    close = data['close'].astype('f8')
    high = data['high'].astype('f8')
    low = data['low'].astype('f8')
    open_ = data['open'].astype('f8')
    volume = data['volume'].astype('f8')
    trades = data['trades'].astype('f8')
    taker_buy = data['taker_buy_vol'].astype('f8')
    
    # 2. Generate all signals
    AS = AlphaSignals
    signal_funcs = {
        'RSI_MeanRevert': lambda: AS.sig_rsi_mean_reversion(close),
        'RSI_Momentum': lambda: AS.sig_rsi_momentum(close),
        'MACD_Crossover': lambda: AS.sig_macd_crossover(close),
        'Price_Momentum_10': lambda: AS.sig_price_momentum(close, 10),
        'Price_Momentum_20': lambda: AS.sig_price_momentum(close, 20),
        'Bollinger_Squeeze': lambda: AS.sig_bollinger_squeeze(close),
        'VWAP_Distance': lambda: AS.sig_distance_from_vwap(close, volume),
        'ATR_Breakout': lambda: AS.sig_atr_breakout(high, low, close),
        'Vol_Contraction': lambda: AS.sig_volatility_contraction(high, low, close),
        'Volume_Spike': lambda: AS.sig_volume_spike(close, volume),
        'OBV_Trend': lambda: AS.sig_obv_trend(close, volume),
        'Taker_Buy_Ratio': lambda: AS.sig_taker_buy_ratio(taker_buy, volume),
        'Trade_Intensity': lambda: AS.sig_trade_intensity(trades),
        'EMA_Cascade': lambda: AS.sig_ema_cascade(close),
        'Higher_Highs': lambda: AS.sig_higher_highs(high, low),
        'Candle_Body': lambda: AS.sig_candle_body_ratio(open_, high, low, close),
        'Gap_Fill': lambda: AS.sig_gap_fill(open_, close),
        'Multi_TF_Mom': lambda: AS.sig_multi_tf_momentum(close),
        'Regime_Filter': lambda: AS.sig_regime_filter(close, high, low),
        'Z_Score': lambda: AS.sig_z_score(close),
    }
    
    logger.info(f"🔬 Testing {len(signal_funcs)} signals...")
    
    # 3. Test each signal
    tester = SignalTester(forward_bars=args.forward)
    results = []
    signals_data = {}
    
    for name, func in signal_funcs.items():
        try:
            sig = func()
            signals_data[name] = sig
            result = tester.test_signal(name, sig, close)
            results.append(result)
            logger.info(f"  {name}: IC={result.ic:+.4f} HR={result.hit_rate:.1f}% Sharpe={result.sharpe:.1f}")
        except Exception as e:
            logger.warning(f"  ⚠️ {name}: {e}")
    
    # 4. Generate report
    generate_report(results, args.symbol, args.days, args.top)
    
    # 5. Correlation matrix of top signals
    ranked = SignalCombiner.rank_signals(results)
    top_names = [r.name for r in ranked[:5]]
    top_sigs = {n: signals_data[n] for n in top_names if n in signals_data}
    
    if len(top_sigs) >= 2:
        print(f"\n📊 CORRELATION MATRIX (top {len(top_sigs)} signals):")
        corr = SignalCombiner.correlation_matrix(top_sigs)
        header = f"{'':>20}" + "".join(f"{n[:12]:>14}" for n in top_sigs.keys())
        print(header)
        for n1, row in corr.items():
            line = f"{n1[:20]:>20}"
            for n2, c in row.items():
                marker = "🔴" if abs(c) > 0.7 else ""
                line += f"{c:>12.3f}{marker:>2}"
            print(line)
    
    # 6. Save
    if args.save:
        save_data = [{
            'name': r.name, 'ic': r.ic, 'hit_rate': r.hit_rate,
            'sharpe': r.sharpe, 'decay': r.decay_half_life, 'turnover': r.turnover
        } for r in ranked]
        with open(args.save, 'w') as f:
            json.dump(save_data, f, indent=2)
        logger.info(f"💾 Saved to {args.save}")


if __name__ == '__main__':
    main()
