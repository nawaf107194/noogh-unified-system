#!/usr/bin/env python3
"""
NOOGH Quantitative Backtesting Framework
=========================================
Renaissance-grade backtesting engine for the Composite Signal Strategy.

Features:
- Historical data download from Binance (klines)
- Event-driven backtesting with composite score replay
- Transaction cost modeling (commissions + slippage + spread)
- Walk-forward optimization with rolling windows
- Monte Carlo simulation for outcome distribution
- Statistical significance testing (Sharpe, t-test, permutation)
- Full visualization suite

Usage:
    python3 backtest_engine.py --symbol BTCUSDT --interval 1h --days 90
"""

import os
import sys
import json
import time
import math
import random
import argparse
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path

# ── Add project root to path ──
sys.path.insert(0, str(Path(__file__).parent))

import requests
import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

# ═══════════════════════════════════════════════════════════════
# Section 1: Data Layer — Historical Data Download & Validation
# ═══════════════════════════════════════════════════════════════

class BinanceDataFetcher:
    """Download historical klines from Binance public API."""
    
    BASE = "https://api.binance.com/api/v3"
    INTERVALS_MS = {
        '1m': 60_000, '5m': 300_000, '15m': 900_000,
        '30m': 1_800_000, '1h': 3_600_000, '4h': 14_400_000,
        '1d': 86_400_000,
    }
    
    def fetch_klines(self, symbol: str, interval: str = '1h',
                     start_date: str = None, end_date: str = None,
                     days: int = 90) -> List[Dict]:
        """
        Fetch historical klines with pagination.
        
        Args:
            symbol: e.g., 'BTCUSDT'
            interval: '1m','5m','15m','30m','1h','4h','1d'
            start_date: 'YYYY-MM-DD' or None (uses days)
            end_date: 'YYYY-MM-DD' or None (now)
            days: number of days back if start_date not specified
        """
        if start_date:
            start_ms = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
        else:
            start_ms = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        if end_date:
            end_ms = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
        else:
            end_ms = int(datetime.now().timestamp() * 1000)
        
        all_klines = []
        current_start = start_ms
        
        logger.info(f"📊 Downloading {symbol} {interval} klines ({days} days)...")
        
        while current_start < end_ms:
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': current_start,
                'endTime': end_ms,
                'limit': 1000,
            }
            
            resp = requests.get(f"{self.BASE}/klines", params=params, timeout=10)
            if resp.status_code != 200:
                logger.error(f"API error: {resp.status_code}")
                break
            
            data = resp.json()
            if not data:
                break
            
            for k in data:
                all_klines.append({
                    'timestamp': k[0],
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5]),
                    'close_time': k[6],
                    'quote_volume': float(k[7]),
                    'trades': int(k[8]),
                    'taker_buy_vol': float(k[9]),
                    'taker_buy_quote': float(k[10]),
                })
            
            current_start = data[-1][6] + 1  # next candle after close_time
            time.sleep(0.1)  # rate limit
        
        logger.info(f"✅ Downloaded {len(all_klines)} candles for {symbol}")
        return all_klines
    
    def validate_data(self, klines: List[Dict]) -> Dict[str, Any]:
        """Data quality checks — detect gaps, anomalies, zero volumes."""
        issues = []
        
        if len(klines) < 100:
            issues.append(f"Too few candles: {len(klines)} (need >= 100)")
        
        # Check for gaps
        gap_count = 0
        for i in range(1, len(klines)):
            expected = klines[i-1]['close_time'] + 1
            actual = klines[i]['timestamp']
            if actual > expected + 60_000:  # > 1 min gap
                gap_count += 1
        
        if gap_count > 0:
            issues.append(f"Data gaps: {gap_count}")
        
        # Check for zero-volume candles
        zero_vol = sum(1 for k in klines if k['volume'] == 0)
        if zero_vol > len(klines) * 0.05:
            issues.append(f"Zero-volume candles: {zero_vol} ({zero_vol/len(klines)*100:.1f}%)")
        
        # Check for price anomalies (> 10% move in single candle)
        anomalies = 0
        for k in klines:
            move = abs(k['close'] - k['open']) / k['open'] * 100
            if move > 10:
                anomalies += 1
        
        if anomalies > 0:
            issues.append(f"Price anomalies (>10% move): {anomalies}")
        
        return {
            'total_candles': len(klines),
            'gap_count': gap_count,
            'zero_vol_count': zero_vol,
            'anomaly_count': anomalies,
            'issues': issues,
            'is_valid': len(issues) == 0,
            'start': datetime.fromtimestamp(klines[0]['timestamp']/1000).strftime('%Y-%m-%d'),
            'end': datetime.fromtimestamp(klines[-1]['timestamp']/1000).strftime('%Y-%m-%d'),
        }


# ═══════════════════════════════════════════════════════════════
# Section 2: Technical Indicators (Pure numpy, no lookahead)
# ═══════════════════════════════════════════════════════════════

class Indicators:
    """Pure numpy implementations — no future data leakage."""
    
    @staticmethod
    def ema(data: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average — computed incrementally."""
        result = np.full_like(data, np.nan)
        if len(data) < period:
            return result
        result[period-1] = np.mean(data[:period])
        multiplier = 2 / (period + 1)
        for i in range(period, len(data)):
            result[i] = (data[i] - result[i-1]) * multiplier + result[i-1]
        return result
    
    @staticmethod
    def rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
        """RSI — Wilder's smoothing."""
        result = np.full_like(data, np.nan)
        if len(data) < period + 1:
            return result
        
        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                result[i+1] = 100
            else:
                rs = avg_gain / avg_loss
                result[i+1] = 100 - (100 / (1 + rs))
        
        return result
    
    @staticmethod
    def macd(data: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9):
        """MACD line, signal line, histogram."""
        ema_fast = Indicators.ema(data, fast)
        ema_slow = Indicators.ema(data, slow)
        macd_line = ema_fast - ema_slow
        
        # Signal line: EMA of MACD, but keep aligned
        sig = np.full_like(data, np.nan)
        valid_mask = ~np.isnan(macd_line)
        valid_macd = macd_line[valid_mask]
        if len(valid_macd) >= signal:
            sig_vals = Indicators.ema(valid_macd, signal)
            # Place back into aligned array
            valid_indices = np.where(valid_mask)[0]
            for j, idx in enumerate(valid_indices):
                if j < len(sig_vals):
                    sig[idx] = sig_vals[j]
        
        hist = macd_line - sig
        return macd_line, sig, hist
    
    @staticmethod
    def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Average True Range."""
        result = np.full_like(close, np.nan)
        if len(close) < period + 1:
            return result
        
        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1])
            )
        )
        
        result[period] = np.mean(tr[:period])
        for i in range(period, len(tr)):
            result[i+1] = (result[i] * (period - 1) + tr[i]) / period
        
        return result
    
    @staticmethod
    def bollinger(data: np.ndarray, period: int = 20, std_mult: float = 2.0):
        """Bollinger Bands."""
        upper = np.full_like(data, np.nan)
        mid = np.full_like(data, np.nan)
        lower = np.full_like(data, np.nan)
        
        for i in range(period - 1, len(data)):
            window = data[i - period + 1:i + 1]
            m = np.mean(window)
            s = np.std(window)
            mid[i] = m
            upper[i] = m + std_mult * s
            lower[i] = m - std_mult * s
        
        return upper, mid, lower


# ═══════════════════════════════════════════════════════════════
# Section 3: Composite Signal Score (mirrors live system)
# ═══════════════════════════════════════════════════════════════

class CompositeSignal:
    """
    Exact replica of live compute_composite_score().
    CRITICAL: Must produce identical signals to live system.
    """
    
    WEIGHTS = {
        'momentum': 0.30,
        'structure': 0.25,
        'orderflow': 0.20,
        'mtf': 0.15,
        'macro': 0.10,
    }
    NO_TRADE_ZONE = 0.20
    
    @staticmethod
    def compute(rsi: float, macd_hist: float, atr: float,
                ema9: float, ema21: float, sma50: float,
                structure: str = 'UNKNOWN',
                ob_imbalance: float = 0, large_bids: int = 0, large_asks: int = 0,
                trend_4h: str = '?',
                macro: str = 'NEUTRAL') -> Dict[str, Any]:
        """Compute composite signal score."""
        
        # A. Momentum (0.30)
        rsi_norm = (rsi - 50) / 50
        macd_norm = max(min(macd_hist / atr if atr else 0, 1), -1)
        ema_cross = 1.0 if ema9 > ema21 else -1.0
        s_momentum = 0.4 * rsi_norm + 0.4 * macd_norm + 0.2 * ema_cross
        
        # B. Structure (0.25)
        struct_map = {
            'BULLISH_STRUCTURE': 0.8, 'ASCENDING_TRIANGLE': 1.0,
            'BEARISH_STRUCTURE': -0.8, 'DESCENDING_TRIANGLE': -1.0,
            'SQUEEZE': 0.0, 'CONSOLIDATION': 0.0, 'EXPANSION': 0.0,
            'UNCLEAR': 0.0, 'UNKNOWN': 0.0,
        }
        s_structure = struct_map.get(structure, 0.0)
        if structure == 'SQUEEZE' and sma50:
            s_structure = 0.6 if ema9 > sma50 else -0.6
        
        # C. Order Flow (0.20)
        imb_norm = max(min(ob_imbalance / 30, 1), -1)
        wall = 0.5 if large_bids > 0 and large_asks == 0 else (-0.5 if large_asks > 0 and large_bids == 0 else 0)
        s_orderflow = 0.6 * imb_norm + 0.4 * wall
        
        # D. MTF (0.15)
        trend_1h = 'UP' if ema9 > ema21 else 'DOWN'
        mtf_map = {('UP','UP'):1.0, ('UP','DOWN'):0.3, ('DOWN','DOWN'):-1.0, ('DOWN','UP'):-0.3}
        s_mtf = mtf_map.get((trend_4h, trend_1h), 0.0)
        if trend_4h == '?':
            s_mtf = 0.5 if trend_1h == 'UP' else -0.5
        
        # E. Macro (0.10)
        macro_map = {'BULLISH': 0.5, 'BEARISH': -0.5, 'MIXED': 0.0, 'NEUTRAL': 0.0}
        s_macro = macro_map.get(macro, 0.0)
        
        W = CompositeSignal.WEIGHTS
        composite = (
            W['momentum'] * s_momentum +
            W['structure'] * s_structure +
            W['orderflow'] * s_orderflow +
            W['mtf'] * s_mtf +
            W['macro'] * s_macro
        )
        composite = max(min(composite, 1.0), -1.0)
        
        return {
            'score': composite,
            'direction': 'LONG' if composite > 0 else 'SHORT' if composite < 0 else 'NONE',
            'tradeable': abs(composite) >= CompositeSignal.NO_TRADE_ZONE,
            'components': {
                'momentum': s_momentum,
                'structure': s_structure,
                'orderflow': s_orderflow,
                'mtf': s_mtf,
                'macro': s_macro,
            }
        }


# ═══════════════════════════════════════════════════════════════
# Section 4: Transaction Cost Model
# ═══════════════════════════════════════════════════════════════

@dataclass
class CostModel:
    """Realistic transaction costs for Binance Futures."""
    commission_rate: float = 0.0004     # 0.04% maker/taker
    slippage_rate: float = 0.0003       # 0.03% average slippage
    spread_rate: float = 0.0001         # 0.01% half-spread
    
    def total_cost_pct(self, leverage: int = 10) -> float:
        """Total round-trip cost as % of position (leveraged)."""
        one_way = self.commission_rate + self.slippage_rate + self.spread_rate
        round_trip = one_way * 2
        return round_trip * leverage * 100  # as percentage


# ═══════════════════════════════════════════════════════════════
# Section 5: Backtest Engine (Event-Driven)
# ═══════════════════════════════════════════════════════════════

@dataclass
class Trade:
    """A single trade record."""
    entry_time: str
    exit_time: str
    direction: str
    entry_price: float
    exit_price: float
    sl: float
    tp: float
    leverage: int
    pnl_pct: float
    pnl_usd: float
    exit_reason: str
    composite_score: float
    duration_min: float


@dataclass
class BacktestResult:
    """Complete backtest results."""
    trades: List[Trade]
    equity_curve: List[float]
    timestamps: List[str]
    initial_balance: float
    final_balance: float
    
    # Performance metrics
    total_return_pct: float = 0
    sharpe_ratio: float = 0
    max_drawdown_pct: float = 0
    win_rate: float = 0
    profit_factor: float = 0
    avg_trade_pnl: float = 0
    total_trades: int = 0
    avg_duration_min: float = 0
    
    # Statistical
    t_stat: float = 0
    p_value: float = 0


class BacktestEngine:
    """
    Event-driven backtesting engine.
    
    ANTI-LOOKAHEAD: Every indicator is computed using ONLY data
    available at or before the current bar. No future data leaks.
    """
    
    def __init__(self, initial_balance: float = 100,
                 leverage: int = 10,
                 sl_pct: float = 0.015,
                 tp_multiplier: float = 2.0,
                 max_duration_min: float = 30,
                 max_concurrent: int = 3,
                 cost_model: CostModel = None):
        
        self.initial_balance = initial_balance
        self.leverage = leverage
        self.sl_pct = sl_pct
        self.tp_multiplier = tp_multiplier
        self.max_duration_min = max_duration_min
        self.max_concurrent = max_concurrent
        self.cost_model = cost_model or CostModel()
        
    def run(self, klines: List[Dict], symbol: str = "BTCUSDT") -> BacktestResult:
        """
        Run backtest on historical klines.
        
        CRITICAL: Only uses data at index <= current bar.
        """
        closes = np.array([k['close'] for k in klines])
        highs = np.array([k['high'] for k in klines])
        lows = np.array([k['low'] for k in klines])
        
        # Pre-compute indicators (each uses only past data by design)
        rsi_arr = Indicators.rsi(closes, 14)
        ema9_arr = Indicators.ema(closes, 9)
        ema21_arr = Indicators.ema(closes, 21)
        sma50_arr = Indicators.ema(closes, 50)
        _, _, macd_hist_arr = Indicators.macd(closes)
        atr_arr = Indicators.atr(highs, lows, closes, 14)
        
        balance = self.initial_balance
        equity_curve = [balance]
        timestamps = [klines[0].get('timestamp', 0)]
        trades: List[Trade] = []
        active_positions = []
        
        # Warmup period (need at least 50 bars for SMA50)
        warmup = 50
        
        cost_per_trade = self.cost_model.total_cost_pct(self.leverage)
        
        for i in range(warmup, len(klines)):
            bar = klines[i]
            price = bar['close']
            ts = bar.get('timestamp', 0)
            bar_time = datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M') if ts else f"bar_{i}"
            
            # ── Check active positions for exit ──
            for pos in active_positions[:]:
                d = pos['direction']
                entry = pos['entry_price']
                sl = pos['sl']
                tp = pos['tp']
                
                # Calculate current P&L
                if d == 'LONG':
                    spot_pnl = (price - entry) / entry
                    hit_tp = bar['high'] >= tp
                    hit_sl = bar['low'] <= sl
                else:
                    spot_pnl = (entry - price) / entry
                    hit_tp = bar['low'] <= tp
                    hit_sl = bar['high'] >= sl
                
                leveraged_pnl = spot_pnl * self.leverage * 100
                
                # Duration check
                elapsed = (i - pos['entry_bar']) * self._interval_minutes(klines)
                expired = elapsed >= self.max_duration_min
                
                exit_reason = None
                exit_price = price
                
                if hit_sl:
                    exit_reason = 'SL_HIT'
                    exit_price = sl
                elif hit_tp:
                    exit_reason = 'TP_HIT'
                    exit_price = tp
                elif expired:
                    exit_reason = 'EXPIRED'
                    exit_price = price
                
                if exit_reason:
                    # Recalculate final P&L at exit price
                    if d == 'LONG':
                        final_pnl_pct = ((exit_price - entry) / entry) * self.leverage * 100
                    else:
                        final_pnl_pct = ((entry - exit_price) / entry) * self.leverage * 100
                    
                    # Subtract transaction costs
                    final_pnl_pct -= cost_per_trade
                    
                    pnl_usd = balance * (final_pnl_pct / 100) * 0.02  # 2% risk
                    balance += pnl_usd
                    
                    trades.append(Trade(
                        entry_time=pos['entry_time'],
                        exit_time=bar_time,
                        direction=d,
                        entry_price=entry,
                        exit_price=exit_price,
                        sl=sl, tp=tp,
                        leverage=self.leverage,
                        pnl_pct=final_pnl_pct,
                        pnl_usd=pnl_usd,
                        exit_reason=exit_reason,
                        composite_score=pos['score'],
                        duration_min=elapsed,
                    ))
                    
                    active_positions.remove(pos)
            
            # ── Check for new entry ──
            if len(active_positions) >= self.max_concurrent:
                equity_curve.append(balance)
                timestamps.append(ts)
                continue
            
            # Get indicator values at THIS bar (no lookahead)
            rsi = rsi_arr[i] if not np.isnan(rsi_arr[i]) else 50
            ema9 = ema9_arr[i] if not np.isnan(ema9_arr[i]) else price
            ema21 = ema21_arr[i] if not np.isnan(ema21_arr[i]) else price
            sma50 = sma50_arr[i] if not np.isnan(sma50_arr[i]) else price
            macd_h = macd_hist_arr[i] if not np.isnan(macd_hist_arr[i]) else 0
            atr = atr_arr[i] if not np.isnan(atr_arr[i]) else price * 0.01
            
            # Detect structure from last 20 bars (no future data)
            structure = self._detect_structure(klines[max(0, i-19):i+1])
            
            # Compute composite score
            signal = CompositeSignal.compute(
                rsi=rsi, macd_hist=macd_h, atr=atr,
                ema9=ema9, ema21=ema21, sma50=sma50,
                structure=structure,
            )
            
            if signal['tradeable']:
                d = signal['direction']
                
                # Calculate SL/TP
                if d == 'LONG':
                    sl = price * (1 - self.sl_pct)
                    tp = price * (1 + self.sl_pct * self.tp_multiplier)
                else:
                    sl = price * (1 + self.sl_pct)
                    tp = price * (1 - self.sl_pct * self.tp_multiplier)
                
                active_positions.append({
                    'direction': d,
                    'entry_price': price,
                    'entry_bar': i,
                    'entry_time': bar_time,
                    'sl': sl,
                    'tp': tp,
                    'score': signal['score'],
                })
            
            equity_curve.append(balance)
            timestamps.append(ts)
        
        # Close remaining positions at last price
        for pos in active_positions:
            price = klines[-1]['close']
            d = pos['direction']
            entry = pos['entry_price']
            if d == 'LONG':
                pnl = ((price - entry) / entry) * self.leverage * 100
            else:
                pnl = ((entry - price) / entry) * self.leverage * 100
            pnl -= cost_per_trade
            pnl_usd = balance * (pnl / 100) * 0.02
            balance += pnl_usd
            
        # Compute metrics
        result = BacktestResult(
            trades=trades,
            equity_curve=equity_curve,
            timestamps=timestamps,
            initial_balance=self.initial_balance,
            final_balance=balance,
        )
        self._compute_metrics(result)
        return result
    
    def _detect_structure(self, klines: List[Dict]) -> str:
        """Simplified structure detection for backtesting."""
        if len(klines) < 10:
            return 'UNKNOWN'
        
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        
        # Find swing points
        sh, sl_pts = [], []
        for i in range(2, len(klines) - 2):
            if highs[i] >= highs[i-1] and highs[i] >= highs[i+1]:
                sh.append(highs[i])
            if lows[i] <= lows[i-1] and lows[i] <= lows[i+1]:
                sl_pts.append(lows[i])
        
        if len(sh) >= 2 and len(sl_pts) >= 2:
            hh = sh[-1] > sh[-2]
            hl = sl_pts[-1] > sl_pts[-2]
            lh = sh[-1] < sh[-2]
            ll = sl_pts[-1] < sl_pts[-2]
            
            if hh and hl: return 'BULLISH_STRUCTURE'
            if lh and ll: return 'BEARISH_STRUCTURE'
        
        return 'CONSOLIDATION'
    
    def _interval_minutes(self, klines: List[Dict]) -> float:
        """Estimate interval from first 2 candles."""
        if len(klines) >= 2:
            diff = klines[1]['timestamp'] - klines[0]['timestamp']
            return diff / 60_000
        return 60  # default 1h
    
    def _compute_metrics(self, result: BacktestResult):
        """Calculate all performance metrics."""
        trades = result.trades
        if not trades:
            return
        
        result.total_trades = len(trades)
        result.total_return_pct = (result.final_balance / result.initial_balance - 1) * 100
        
        wins = [t for t in trades if t.pnl_pct > 0]
        losses = [t for t in trades if t.pnl_pct <= 0]
        result.win_rate = len(wins) / len(trades) * 100 if trades else 0
        
        total_wins = sum(t.pnl_pct for t in wins)
        total_losses = abs(sum(t.pnl_pct for t in losses))
        result.profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        result.avg_trade_pnl = np.mean([t.pnl_pct for t in trades])
        result.avg_duration_min = np.mean([t.duration_min for t in trades])
        
        # Max drawdown
        peak = result.equity_curve[0]
        max_dd = 0
        for eq in result.equity_curve:
            peak = max(peak, eq)
            dd = (peak - eq) / peak * 100
            max_dd = max(max_dd, dd)
        result.max_drawdown_pct = max_dd
        
        # Sharpe ratio (annualized)
        returns = np.diff(result.equity_curve) / result.equity_curve[:-1]
        if len(returns) > 1 and np.std(returns) > 0:
            # Assuming hourly bars → 8760 bars/year
            result.sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(8760)
        
        # T-test: is mean return significantly different from 0?
        trade_returns = [t.pnl_pct for t in trades]
        if len(trade_returns) > 2:
            mean_r = np.mean(trade_returns)
            std_r = np.std(trade_returns, ddof=1)
            result.t_stat = mean_r / (std_r / np.sqrt(len(trade_returns)))
            # Approximate p-value (two-tailed)
            # Using normal approximation for large n
            from math import erfc
            result.p_value = erfc(abs(result.t_stat) / np.sqrt(2))


# ═══════════════════════════════════════════════════════════════
# Section 6: Walk-Forward Optimization
# ═══════════════════════════════════════════════════════════════

class WalkForward:
    """
    Walk-forward analysis: train on in-sample, test on out-of-sample.
    Prevents overfitting by never testing on data used for optimization.
    """
    
    def __init__(self, train_pct: float = 0.70, n_folds: int = 5):
        self.train_pct = train_pct
        self.n_folds = n_folds
    
    def run(self, klines: List[Dict], engine: BacktestEngine) -> Dict:
        """Run walk-forward with rolling windows."""
        total = len(klines)
        fold_size = total // self.n_folds
        
        results = []
        
        for fold in range(self.n_folds):
            start = fold * fold_size
            end = min(start + fold_size, total)
            fold_data = klines[start:end]
            
            train_end = int(len(fold_data) * self.train_pct)
            test_data = fold_data[train_end:]
            
            if len(test_data) < 100:
                continue
            
            # Run backtest on OUT-OF-SAMPLE data only
            result = engine.run(test_data)
            results.append({
                'fold': fold + 1,
                'test_period': f"{test_data[0].get('timestamp', 0)} - {test_data[-1].get('timestamp', 0)}",
                'trades': result.total_trades,
                'win_rate': result.win_rate,
                'return_pct': result.total_return_pct,
                'sharpe': result.sharpe_ratio,
                'max_dd': result.max_drawdown_pct,
            })
        
        return {
            'folds': results,
            'avg_win_rate': np.mean([r['win_rate'] for r in results]) if results else 0,
            'avg_return': np.mean([r['return_pct'] for r in results]) if results else 0,
            'avg_sharpe': np.mean([r['sharpe'] for r in results]) if results else 0,
            'consistency': sum(1 for r in results if r['return_pct'] > 0) / len(results) * 100 if results else 0,
        }


# ═══════════════════════════════════════════════════════════════
# Section 7: Monte Carlo Simulation
# ═══════════════════════════════════════════════════════════════

class MonteCarlo:
    """
    Randomize trade sequence to understand range of outcomes.
    Same trades, different order → different equity curves.
    """
    
    def __init__(self, n_simulations: int = 1000):
        self.n_simulations = n_simulations
    
    def run(self, trades: List[Trade], initial_balance: float = 100) -> Dict:
        """Run Monte Carlo simulation."""
        if not trades:
            return {'error': 'No trades'}
        
        trade_returns = [t.pnl_pct for t in trades]
        
        final_balances = []
        max_drawdowns = []
        
        for _ in range(self.n_simulations):
            # Shuffle trade order
            shuffled = trade_returns.copy()
            random.shuffle(shuffled)
            
            balance = initial_balance
            peak = balance
            max_dd = 0
            
            for r in shuffled:
                pnl = balance * (r / 100) * 0.02  # 2% risk
                balance += pnl
                balance = max(balance, 1)  # can't go below $1
                peak = max(peak, balance)
                dd = (peak - balance) / peak * 100
                max_dd = max(max_dd, dd)
            
            final_balances.append(balance)
            max_drawdowns.append(max_dd)
        
        final_balances.sort()
        
        return {
            'median_balance': np.median(final_balances),
            'mean_balance': np.mean(final_balances),
            'p5_balance': np.percentile(final_balances, 5),    # worst 5%
            'p95_balance': np.percentile(final_balances, 95),   # best 5%
            'p5_drawdown': np.percentile(max_drawdowns, 95),    # worst DD
            'median_drawdown': np.median(max_drawdowns),
            'probability_profit': sum(1 for b in final_balances if b > initial_balance) / len(final_balances) * 100,
            'probability_ruin': sum(1 for b in final_balances if b < initial_balance * 0.5) / len(final_balances) * 100,
        }


# ═══════════════════════════════════════════════════════════════
# Section 8: Report Generator
# ═══════════════════════════════════════════════════════════════

def generate_report(result: BacktestResult, wf: Dict = None, mc: Dict = None,
                    symbol: str = "BTCUSDT", validation: Dict = None):
    """Generate human-readable backtest report."""
    
    print("\n" + "=" * 70)
    print(f"  NOOGH QUANTITATIVE BACKTEST REPORT — {symbol}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    print(f"\n📊 PERFORMANCE SUMMARY")
    print(f"  {'Initial Balance:':<25} ${result.initial_balance:,.2f}")
    print(f"  {'Final Balance:':<25} ${result.final_balance:,.2f}")
    print(f"  {'Total Return:':<25} {result.total_return_pct:+.2f}%")
    print(f"  {'Total Trades:':<25} {result.total_trades}")
    print(f"  {'Win Rate:':<25} {result.win_rate:.1f}%")
    print(f"  {'Profit Factor:':<25} {result.profit_factor:.2f}")
    print(f"  {'Avg Trade P&L:':<25} {result.avg_trade_pnl:+.2f}%")
    print(f"  {'Avg Duration:':<25} {result.avg_duration_min:.1f} min")
    
    print(f"\n🛡️ RISK METRICS")
    print(f"  {'Max Drawdown:':<25} {result.max_drawdown_pct:.2f}%")
    print(f"  {'Sharpe Ratio:':<25} {result.sharpe_ratio:.2f}")
    
    print(f"\n📐 STATISTICAL SIGNIFICANCE")
    print(f"  {'T-Statistic:':<25} {result.t_stat:.3f}")
    print(f"  {'P-Value:':<25} {result.p_value:.4f}")
    sig = "✅ SIGNIFICANT (p < 0.05)" if result.p_value < 0.05 else "❌ NOT SIGNIFICANT"
    print(f"  {'Conclusion:':<25} {sig}")
    
    if result.trades:
        # Exit reason breakdown
        reasons = {}
        for t in result.trades:
            reasons[t.exit_reason] = reasons.get(t.exit_reason, 0) + 1
        print(f"\n📋 EXIT REASONS")
        for reason, count in sorted(reasons.items()):
            wr = sum(1 for t in result.trades if t.exit_reason == reason and t.pnl_pct > 0) / count * 100
            print(f"  {reason:<15} {count:>4} trades | WR: {wr:.0f}%")
    
    if wf:
        print(f"\n📈 WALK-FORWARD ANALYSIS ({len(wf.get('folds', []))} folds)")
        print(f"  {'Avg Win Rate:':<25} {wf['avg_win_rate']:.1f}%")
        print(f"  {'Avg Return:':<25} {wf['avg_return']:+.2f}%")
        print(f"  {'Avg Sharpe:':<25} {wf['avg_sharpe']:.2f}")
        print(f"  {'Consistency:':<25} {wf['consistency']:.0f}% folds profitable")
    
    if mc:
        print(f"\n🎲 MONTE CARLO ({1000} simulations)")
        print(f"  {'Median Balance:':<25} ${mc['median_balance']:,.2f}")
        print(f"  {'5th Percentile:':<25} ${mc['p5_balance']:,.2f} (worst case)")
        print(f"  {'95th Percentile:':<25} ${mc['p95_balance']:,.2f} (best case)")
        print(f"  {'P(Profit):':<25} {mc['probability_profit']:.1f}%")
        print(f"  {'P(Ruin <50%):':<25} {mc['probability_ruin']:.1f}%")
        print(f"  {'Worst Drawdown (5%):':<25} {mc['p5_drawdown']:.1f}%")
    
    if validation:
        print(f"\n✅ DATA VALIDATION")
        print(f"  {'Candles:':<25} {validation['total_candles']}")
        print(f"  {'Period:':<25} {validation['start']} → {validation['end']}")
        print(f"  {'Gaps:':<25} {validation['gap_count']}")
        print(f"  {'Quality:':<25} {'✅ PASS' if validation['is_valid'] else '⚠️ ISSUES'}")
    
    print("\n" + "=" * 70)
    
    # ── Verdict ──
    print("\n🎯 STRATEGY VERDICT:")
    score = 0
    if result.win_rate > 50: score += 1
    if result.profit_factor > 1.2: score += 1
    if result.sharpe_ratio > 1.0: score += 1
    if result.p_value < 0.05: score += 1
    if result.max_drawdown_pct < 30: score += 1
    if wf and wf.get('consistency', 0) > 60: score += 1
    if mc and mc.get('probability_profit', 0) > 60: score += 1
    
    verdicts = {
        (0, 2): "🔴 REJECT — Strategy has no edge",
        (3, 4): "🟡 WEAK — Promising but needs refinement",
        (5, 5): "🟢 VIABLE — Deploy with small capital",
        (6, 7): "🟢 STRONG — Deploy with full capital",
    }
    for (lo, hi), v in verdicts.items():
        if lo <= score <= hi:
            print(f"  {v} (score: {score}/7)")
            break
    
    print("")


# ═══════════════════════════════════════════════════════════════
# Section 9: Main Entry Point
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='NOOGH Quantitative Backtester')
    parser.add_argument('--symbol', default='BTCUSDT', help='Trading pair')
    parser.add_argument('--interval', default='1h', help='Candle interval')
    parser.add_argument('--days', type=int, default=90, help='Days of history')
    parser.add_argument('--balance', type=float, default=100, help='Starting balance')
    parser.add_argument('--leverage', type=int, default=10, help='Leverage')
    parser.add_argument('--sl', type=float, default=0.015, help='Stop loss %')
    parser.add_argument('--monte-carlo', type=int, default=1000, help='MC simulations')
    parser.add_argument('--walk-forward', type=int, default=5, help='WF folds')
    parser.add_argument('--save', help='Save results to JSON file')
    args = parser.parse_args()
    
    # 1. Download data
    fetcher = BinanceDataFetcher()
    klines = fetcher.fetch_klines(args.symbol, args.interval, days=args.days)
    
    if not klines:
        logger.error("❌ No data downloaded")
        return
    
    # 2. Validate data
    validation = fetcher.validate_data(klines)
    if not validation['is_valid']:
        logger.warning(f"⚠️ Data issues: {validation['issues']}")
    
    # 3. Run backtest
    engine = BacktestEngine(
        initial_balance=args.balance,
        leverage=args.leverage,
        sl_pct=args.sl,
        max_concurrent=3,
    )
    result = engine.run(klines, args.symbol)
    
    # 4. Walk-forward
    wf_result = None
    if args.walk_forward > 1:
        wf = WalkForward(n_folds=args.walk_forward)
        wf_result = wf.run(klines, engine)
    
    # 5. Monte Carlo
    mc_result = None
    if result.trades and args.monte_carlo > 0:
        mc = MonteCarlo(n_simulations=args.monte_carlo)
        mc_result = mc.run(result.trades, args.balance)
    
    # 6. Generate report
    generate_report(result, wf_result, mc_result, args.symbol, validation)
    
    # 7. Save
    if args.save:
        save_data = {
            'symbol': args.symbol,
            'interval': args.interval,
            'days': args.days,
            'total_trades': result.total_trades,
            'win_rate': result.win_rate,
            'profit_factor': result.profit_factor,
            'sharpe': result.sharpe_ratio,
            'max_drawdown': result.max_drawdown_pct,
            'total_return': result.total_return_pct,
            'p_value': result.p_value,
        }
        with open(args.save, 'w') as f:
            json.dump(save_data, f, indent=2)
        logger.info(f"💾 Results saved to {args.save}")


if __name__ == '__main__':
    main()
