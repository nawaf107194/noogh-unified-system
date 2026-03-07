#!/usr/bin/env python3
"""
NOOGH Statistical Arbitrage — Pairs Trading
=============================================
D.E. Shaw-style stat-arb framework for crypto pairs.

Features:
- Pair screening: correlation + cointegration across all crypto pairs
- Engle-Granger cointegration test
- Hedge ratio via OLS regression
- Z-score signal generation
- Mean reversion speed (half-life)
- Regime change detection (rolling cointegration p-value)
- Multi-pair portfolio with capital allocation
- Backtest with transaction costs

Usage:
    python3 stat_arb.py --days 90
    python3 stat_arb.py --pair ETHUSDT:BTCUSDT --days 60
"""

import sys
import time
import json
import argparse
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from itertools import combinations

import numpy as np
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')

SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'AVAXUSDT', 'DOGEUSDT']


# ═══════════════════════════════════════════════════════════════
# Section 1: Data
# ═══════════════════════════════════════════════════════════════

def fetch_klines(symbol: str, interval: str = '1h', days: int = 90) -> np.ndarray:
    """Fetch from Binance, return close prices."""
    BASE = "https://api.binance.com/api/v3"
    start = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    end = int(datetime.now().timestamp() * 1000)
    closes, timestamps = [], []
    current = start
    while current < end:
        r = requests.get(f"{BASE}/klines", params={
            'symbol': symbol, 'interval': interval,
            'startTime': current, 'endTime': end, 'limit': 1000
        }, timeout=10)
        if r.status_code != 200: break
        data = r.json()
        if not data: break
        for k in data:
            closes.append(float(k[4]))
            timestamps.append(k[0])
        current = data[-1][6] + 1
        time.sleep(0.1)
    return np.array(closes), timestamps


def fetch_all(symbols: List[str], interval: str = '1h', days: int = 90) -> Dict[str, np.ndarray]:
    """Fetch all symbols, align by length."""
    data = {}
    min_len = float('inf')
    logger.info(f"📊 Downloading {len(symbols)} pairs ({days} days)...")
    for s in symbols:
        closes, _ = fetch_klines(s, interval, days)
        if len(closes) > 0:
            data[s] = closes
            min_len = min(min_len, len(closes))
    # Trim to same length
    for s in list(data.keys()):
        data[s] = data[s][-int(min_len):]
    logger.info(f"✅ {len(data)} pairs, {int(min_len)} aligned candles each")
    return data


# ═══════════════════════════════════════════════════════════════
# Section 2: Statistical Tests
# ═══════════════════════════════════════════════════════════════

def adf_test(series: np.ndarray) -> Tuple[float, float]:
    """
    Augmented Dickey-Fuller test for stationarity.
    Returns (test_statistic, p_value).
    
    H0: series has a unit root (non-stationary)
    If p < 0.05: reject H0 → series is stationary → good for mean reversion
    
    Implementation: OLS regression of Δy on y_{t-1} + constant
    """
    if len(series) < 20:
        return 0.0, 1.0
    
    y = series[1:]
    y_lag = series[:-1]
    dy = np.diff(series)
    
    n = len(dy)
    
    # OLS: dy = alpha + beta * y_lag + epsilon
    X = np.column_stack([np.ones(n), y_lag])
    try:
        beta = np.linalg.lstsq(X, dy, rcond=None)[0]
        residuals = dy - X @ beta
        se = np.sqrt(np.sum(residuals**2) / (n - 2))
        se_beta = se / np.sqrt(np.sum((y_lag - np.mean(y_lag))**2))
        t_stat = beta[1] / se_beta if se_beta > 0 else 0
    except Exception:
        return 0.0, 1.0
    
    # MacKinnon critical values (approximation for n > 100)
    # 1%: -3.43, 5%: -2.86, 10%: -2.57
    if t_stat < -3.43:
        p_value = 0.01
    elif t_stat < -2.86:
        p_value = 0.05
    elif t_stat < -2.57:
        p_value = 0.10
    elif t_stat < -1.94:
        p_value = 0.20
    else:
        p_value = 0.50 + min(t_stat * 0.1, 0.49)
    
    return round(t_stat, 4), round(max(0, min(p_value, 1.0)), 4)


def engle_granger_coint(y1: np.ndarray, y2: np.ndarray) -> Dict:
    """
    Engle-Granger two-step cointegration test.
    
    Step 1: Regress y1 = α + β × y2 + ε
    Step 2: Test residuals for stationarity (ADF test)
    
    If residuals are stationary → y1 and y2 are cointegrated.
    """
    n = min(len(y1), len(y2))
    y1, y2 = y1[:n], y2[:n]
    
    # Step 1: OLS regression
    X = np.column_stack([np.ones(n), y2])
    coeffs = np.linalg.lstsq(X, y1, rcond=None)[0]
    alpha, beta = coeffs[0], coeffs[1]
    
    # Residuals = spread
    residuals = y1 - (alpha + beta * y2)
    
    # Step 2: ADF on residuals
    adf_stat, p_value = adf_test(residuals)
    
    # Correlation
    corr = np.corrcoef(y1, y2)[0, 1]
    
    return {
        'alpha': round(alpha, 6),
        'beta': round(beta, 6),          # Hedge ratio
        'adf_stat': adf_stat,
        'p_value': p_value,
        'correlation': round(corr, 4),
        'is_cointegrated': p_value < 0.05,
        'residuals': residuals,
    }


def half_life(spread: np.ndarray) -> float:
    """
    Mean reversion half-life via AR(1).
    
    spread_t = φ × spread_{t-1} + ε
    half_life = -ln(2) / ln(φ)
    
    Shorter = faster mean reversion = better for trading.
    """
    if len(spread) < 10:
        return float('inf')
    
    y = spread[1:]
    y_lag = spread[:-1]
    
    X = np.column_stack([np.ones(len(y_lag)), y_lag])
    try:
        coeffs = np.linalg.lstsq(X, y, rcond=None)[0]
        phi = coeffs[1]
        if phi <= 0 or phi >= 1:
            return float('inf')
        return -np.log(2) / np.log(phi)
    except:
        return float('inf')


# ═══════════════════════════════════════════════════════════════
# Section 3: Z-Score Signal Generator
# ═══════════════════════════════════════════════════════════════

@dataclass
class PairConfig:
    sym1: str
    sym2: str
    hedge_ratio: float
    alpha: float
    entry_z: float = 2.0       # Open position at ±2σ
    exit_z: float = 0.5        # Close at ±0.5σ
    stop_z: float = 4.0        # Stop loss at ±4σ
    lookback: int = 20         # Rolling Z-score window


class ZScoreEngine:
    """Generate Z-score based trading signals for a pair."""
    
    def __init__(self, config: PairConfig):
        self.config = config
    
    def compute_spread(self, y1: np.ndarray, y2: np.ndarray) -> np.ndarray:
        """Spread = Y1 - (alpha + beta × Y2)."""
        return y1 - (self.config.alpha + self.config.hedge_ratio * y2)
    
    def compute_zscore(self, spread: np.ndarray) -> np.ndarray:
        """Rolling Z-score of spread."""
        z = np.full_like(spread, np.nan)
        lb = self.config.lookback
        for i in range(lb, len(spread)):
            window = spread[i - lb:i]
            m, s = np.mean(window), np.std(window)
            if s > 0:
                z[i] = (spread[i] - m) / s
        return z
    
    def generate_signals(self, y1: np.ndarray, y2: np.ndarray) -> np.ndarray:
        """
        Generate signals:
          +1 = SHORT spread (short Y1, long Y2) — spread too high
          -1 = LONG spread (long Y1, short Y2) — spread too low
           0 = no position / close
        """
        spread = self.compute_spread(y1, y2)
        z = self.compute_zscore(spread)
        
        signals = np.zeros(len(z))
        position = 0
        
        for i in range(len(z)):
            if np.isnan(z[i]):
                continue
            
            if position == 0:
                # Entry
                if z[i] > self.config.entry_z:
                    position = -1  # SHORT spread
                elif z[i] < -self.config.entry_z:
                    position = 1   # LONG spread
            elif position == 1:
                # Long spread, exit when reverts or stop
                if z[i] > -self.config.exit_z:
                    position = 0   # Mean reverted
                elif z[i] < -self.config.stop_z:
                    position = 0   # Stop loss
            elif position == -1:
                # Short spread, exit when reverts or stop
                if z[i] < self.config.exit_z:
                    position = 0   # Mean reverted
                elif z[i] > self.config.stop_z:
                    position = 0   # Stop loss
            
            signals[i] = position
        
        return signals, spread, z


# ═══════════════════════════════════════════════════════════════
# Section 4: Regime Change Detector
# ═══════════════════════════════════════════════════════════════

class RegimeDetector:
    """Detect when a pair relationship breaks down."""
    
    def __init__(self, rolling_window: int = 120, threshold: float = 0.10):
        self.window = rolling_window
        self.threshold = threshold
    
    def check(self, y1: np.ndarray, y2: np.ndarray) -> Dict:
        """Rolling cointegration status."""
        n = len(y1)
        if n < self.window + 20:
            return {'status': 'INSUFFICIENT_DATA'}
        
        # Test current window
        recent_y1 = y1[-self.window:]
        recent_y2 = y2[-self.window:]
        result = engle_granger_coint(recent_y1, recent_y2)
        
        # Test earlier window for comparison
        earlier_y1 = y1[-(self.window*2):-(self.window)]
        earlier_y2 = y2[-(self.window*2):-(self.window)]
        if len(earlier_y1) >= 50:
            earlier = engle_granger_coint(earlier_y1, earlier_y2)
        else:
            earlier = {'p_value': 1.0, 'beta': 0}
        
        # Hedge ratio stability
        beta_change = abs(result['beta'] - earlier['beta']) / abs(earlier['beta']) if earlier['beta'] != 0 else 0
        
        if result['p_value'] > 0.10:
            status = '🔴 BROKEN'
        elif result['p_value'] > 0.05:
            status = '🟡 WEAKENING'
        elif beta_change > 0.3:
            status = '🟡 UNSTABLE_HEDGE'
        else:
            status = '🟢 STABLE'
        
        return {
            'status': status,
            'current_p': result['p_value'],
            'current_beta': result['beta'],
            'earlier_p': earlier['p_value'],
            'earlier_beta': earlier['beta'],
            'beta_drift': round(beta_change * 100, 1),
        }


# ═══════════════════════════════════════════════════════════════
# Section 5: Backtester
# ═══════════════════════════════════════════════════════════════

@dataclass
class PairTrade:
    entry_bar: int
    exit_bar: int
    direction: str       # 'LONG_SPREAD' or 'SHORT_SPREAD'
    entry_z: float
    exit_z: float
    entry_spread: float
    exit_spread: float
    pnl_pct: float
    duration: int


@dataclass
class PairResult:
    pair: str
    trades: List[PairTrade]
    total_return: float
    win_rate: float
    profit_factor: float
    avg_trade: float
    sharpe: float
    max_dd: float
    half_life_bars: float
    cointegrated: bool
    p_value: float
    correlation: float
    hedge_ratio: float
    regime: str


class PairBacktester:
    """Backtest a single pair."""
    
    def __init__(self, commission: float = 0.0004):
        self.commission = commission  # Per side
    
    def run(self, sym1: str, sym2: str, y1: np.ndarray, y2: np.ndarray,
            config: PairConfig) -> PairResult:
        
        engine = ZScoreEngine(config)
        signals, spread, z = engine.generate_signals(y1, y2)
        
        # Calculate half-life
        hl = half_life(spread)
        
        # Cointegration
        coint = engle_granger_coint(y1, y2)
        
        # Regime
        regime = RegimeDetector().check(y1, y2)
        
        # Simulate trades
        trades = []
        position = 0
        entry_bar = 0
        entry_z_val = 0
        entry_spread_val = 0
        
        equity = [0.0]
        
        for i in range(1, len(signals)):
            if signals[i] != signals[i-1]:
                # Position changed
                if signals[i-1] != 0 and position != 0:
                    # Closing
                    exit_spread = spread[i]
                    if position == 1:  # Was long spread
                        pnl = (exit_spread - entry_spread_val) / abs(entry_spread_val) * 100 if entry_spread_val != 0 else 0
                    else:  # Was short spread
                        pnl = (entry_spread_val - exit_spread) / abs(entry_spread_val) * 100 if entry_spread_val != 0 else 0
                    
                    # Subtract costs (4 legs: buy+sell for each symbol)
                    pnl -= self.commission * 4 * 100
                    
                    trades.append(PairTrade(
                        entry_bar=entry_bar, exit_bar=i,
                        direction='LONG_SPREAD' if position == 1 else 'SHORT_SPREAD',
                        entry_z=entry_z_val,
                        exit_z=z[i] if not np.isnan(z[i]) else 0,
                        entry_spread=entry_spread_val,
                        exit_spread=exit_spread,
                        pnl_pct=round(pnl, 4),
                        duration=i - entry_bar,
                    ))
                    equity.append(equity[-1] + pnl)
                    position = 0
                
                if signals[i] != 0:
                    # Opening
                    position = int(signals[i])
                    entry_bar = i
                    entry_z_val = z[i] if not np.isnan(z[i]) else 0
                    entry_spread_val = spread[i]
        
        # Metrics
        if trades:
            wins = [t for t in trades if t.pnl_pct > 0]
            losses = [t for t in trades if t.pnl_pct <= 0]
            total_wins = sum(t.pnl_pct for t in wins)
            total_losses = abs(sum(t.pnl_pct for t in losses))
            
            pnl_arr = np.array([t.pnl_pct for t in trades])
            eq = np.cumsum(pnl_arr)
            peak = np.maximum.accumulate(eq)
            max_dd = np.max(peak - eq) if len(eq) > 0 else 0
            sharpe_val = np.mean(pnl_arr) / np.std(pnl_arr) * np.sqrt(252) if np.std(pnl_arr) > 0 else 0
        else:
            total_wins, total_losses = 0, 0
            wins, losses = [], []
            max_dd = 0
            sharpe_val = 0
        
        return PairResult(
            pair=f"{sym1}/{sym2}",
            trades=trades,
            total_return=round(sum(t.pnl_pct for t in trades), 2) if trades else 0,
            win_rate=round(len(wins)/len(trades)*100, 1) if trades else 0,
            profit_factor=round(total_wins/total_losses, 2) if total_losses > 0 else 0,
            avg_trade=round(np.mean([t.pnl_pct for t in trades]), 4) if trades else 0,
            sharpe=round(sharpe_val, 2),
            max_dd=round(max_dd, 2),
            half_life_bars=round(hl, 1),
            cointegrated=coint['is_cointegrated'],
            p_value=coint['p_value'],
            correlation=coint['correlation'],
            hedge_ratio=coint['beta'],
            regime=regime['status'],
        )


# ═══════════════════════════════════════════════════════════════
# Section 6: Pair Screener & Portfolio
# ═══════════════════════════════════════════════════════════════

class PairScreener:
    """Screen all pairs for cointegration and tradeable properties."""
    
    def screen(self, data: Dict[str, np.ndarray]) -> List[PairResult]:
        """Test all pair combinations."""
        symbols = list(data.keys())
        pairs = list(combinations(symbols, 2))
        
        logger.info(f"🔬 Screening {len(pairs)} pairs...")
        results = []
        
        for sym1, sym2 in pairs:
            y1, y2 = data[sym1], data[sym2]
            
            # Quick cointegration test
            coint = engle_granger_coint(y1, y2)
            
            if coint['p_value'] > 0.20 and abs(coint['correlation']) < 0.5:
                continue  # Skip clearly unrelated pairs
            
            # Full backtest
            config = PairConfig(
                sym1=sym1, sym2=sym2,
                hedge_ratio=coint['beta'],
                alpha=coint['alpha'],
            )
            
            bt = PairBacktester()
            result = bt.run(sym1, sym2, y1, y2, config)
            results.append(result)
        
        # Sort by quality
        results.sort(key=lambda r: (r.cointegrated, r.total_return), reverse=True)
        return results


# ═══════════════════════════════════════════════════════════════
# Section 7: Report
# ═══════════════════════════════════════════════════════════════

def generate_report(results: List[PairResult], days: int):
    print("\n" + "=" * 90)
    print(f"  NOOGH STATISTICAL ARBITRAGE RESEARCH REPORT")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')} | {days} days | {len(results)} pairs analyzed")
    print("=" * 90)
    
    # Cointegrated pairs
    coint_pairs = [r for r in results if r.cointegrated]
    non_coint = [r for r in results if not r.cointegrated]
    
    print(f"\n🔗 COINTEGRATED PAIRS ({len(coint_pairs)}/{len(results)})")
    print(f"{'Pair':<20} {'Corr':<8} {'p-val':<8} {'Hedge β':<10} {'HL(bars)':<10} {'Trades':<8} {'WR%':<8} {'Return%':<10} {'PF':<8} {'Sharpe':<8} {'Regime'}")
    print("-" * 118)
    
    for r in coint_pairs:
        print(f"{r.pair:<20} {r.correlation:>6.3f}  {r.p_value:>6.3f}  {r.hedge_ratio:>8.4f}  {r.half_life_bars:>8.1f}  {len(r.trades):>6}  {r.win_rate:>5.1f}  {r.total_return:>8.2f}  {r.profit_factor:>6.2f}  {r.sharpe:>6.2f}  {r.regime}")
    
    if non_coint:
        print(f"\n⚠️ NON-COINTEGRATED PAIRS ({len(non_coint)})")
        print(f"{'Pair':<20} {'Corr':<8} {'p-val':<8} {'Trades':<8} {'Return%':<10}")
        print("-" * 54)
        for r in non_coint:
            print(f"{r.pair:<20} {r.correlation:>6.3f}  {r.p_value:>6.3f}  {len(r.trades):>6}  {r.total_return:>8.2f}")
    
    # Best pair analysis
    if coint_pairs:
        best = max(coint_pairs, key=lambda r: r.total_return)
        print(f"\n{'─' * 90}")
        print(f"  👑 BEST PAIR: {best.pair}")
        print(f"{'─' * 90}")
        print(f"  Correlation:     {best.correlation:.4f}")
        print(f"  Cointegration:   p={best.p_value:.4f} {'✅ SIGNIFICANT' if best.p_value < 0.05 else '⚠️'}")
        print(f"  Hedge Ratio (β): {best.hedge_ratio:.6f}")
        print(f"  Half-Life:       {best.half_life_bars:.1f} bars")
        print(f"  Total Trades:    {len(best.trades)}")
        print(f"  Win Rate:        {best.win_rate:.1f}%")
        print(f"  Total Return:    {best.total_return:+.2f}%")
        print(f"  Profit Factor:   {best.profit_factor:.2f}")
        print(f"  Sharpe:          {best.sharpe:.2f}")
        print(f"  Max Drawdown:    {best.max_dd:.2f}%")
        print(f"  Regime:          {best.regime}")
        
        if best.trades:
            print(f"\n  Recent trades:")
            for t in best.trades[-5:]:
                marker = "✅" if t.pnl_pct > 0 else "❌"
                print(f"    {marker} {t.direction:<15} Z:{t.entry_z:+.2f}→{t.exit_z:+.2f} | "
                      f"P&L: {t.pnl_pct:+.4f}% | Duration: {t.duration} bars")
    
    # Portfolio recommendation
    print(f"\n{'─' * 90}")
    print(f"  PORTFOLIO RECOMMENDATION")
    print(f"{'─' * 90}")
    
    viable = [r for r in coint_pairs if r.total_return > 0 and r.win_rate > 45]
    if viable:
        total_alloc = sum(abs(r.total_return) for r in viable)
        print(f"\n  ✅ {len(viable)} viable pairs for stat-arb portfolio:")
        for r in viable:
            weight = abs(r.total_return) / total_alloc * 100 if total_alloc > 0 else 100 / len(viable)
            print(f"    • {r.pair}: {weight:.1f}% allocation | β={r.hedge_ratio:.4f} | HL={r.half_life_bars:.0f} bars")
    else:
        print(f"\n  ⚠️ No viable pairs for stat-arb in current market conditions.")
        print(f"  Crypto pairs tend to lose cointegration during regime changes.")
        print(f"  Try: longer history, different timeframes, or sector-specific pairs.")
    
    print("\n" + "=" * 90)


# ═══════════════════════════════════════════════════════════════
# Section 8: Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='NOOGH Stat-Arb Pairs Trading')
    parser.add_argument('--days', type=int, default=90)
    parser.add_argument('--interval', default='1h')
    parser.add_argument('--pair', help='Specific pair: ETHUSDT:BTCUSDT')
    parser.add_argument('--symbols', nargs='+', default=SYMBOLS)
    args = parser.parse_args()
    
    if args.pair:
        # Single pair analysis
        sym1, sym2 = args.pair.split(':')
        y1, _ = fetch_klines(sym1, args.interval, args.days)
        y2, _ = fetch_klines(sym2, args.interval, args.days)
        n = min(len(y1), len(y2))
        y1, y2 = y1[:n], y2[:n]
        
        coint = engle_granger_coint(y1, y2)
        config = PairConfig(sym1=sym1, sym2=sym2, hedge_ratio=coint['beta'], alpha=coint['alpha'])
        bt = PairBacktester()
        result = bt.run(sym1, sym2, y1, y2, config)
        generate_report([result], args.days)
    else:
        # Full pair screening
        data = fetch_all(args.symbols, args.interval, args.days)
        screener = PairScreener()
        results = screener.screen(data)
        generate_report(results, args.days)


if __name__ == '__main__':
    main()
