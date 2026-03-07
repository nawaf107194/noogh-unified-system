#!/usr/bin/env python3
"""
NOOGH Execution Algorithm Engine
===================================
Virtu Financial-style smart execution for crypto futures.

Algorithms:
- TWAP: Time-Weighted Average Price (even time splits)
- VWAP: Volume-Weighted Average Price (follow volume curve)
- Iceberg: Hide true order size, show small slices
- Implementation Shortfall: Balance urgency vs impact

Analytics:
- Slippage measurement
- Market impact model
- Pre-trade cost estimation
- Post-trade TCA (Transaction Cost Analysis)

Usage:
    python3 execution_engine.py simulate --symbol BTCUSDT --size 0.01 --algo twap
    python3 execution_engine.py analyze --symbol BTCUSDT --days 7
"""

import sys
import json
import time
import math
import argparse
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

import numpy as np
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')


# ═══════════════════════════════════════════════════════════════
# Section 1: Market Impact Model
# ═══════════════════════════════════════════════════════════════

class MarketImpactModel:
    """
    Almgren-Chriss market impact model (simplified for crypto).
    
    Total Cost = Spread Cost + Temporary Impact + Permanent Impact
    
    Temporary impact: η × (v/V)^0.6
    Permanent impact: γ × (Q/V)^0.5
    
    Where:
        v = execution rate (coins/min)
        V = market volume (coins/min)
        Q = total order size
        η, γ = impact coefficients (calibrated to market)
    """
    
    def __init__(self, eta: float = 0.0005, gamma: float = 0.0002):
        self.eta = eta       # Temporary impact coefficient
        self.gamma = gamma   # Permanent impact coefficient
    
    def estimate_impact(self, order_size: float, market_volume: float,
                         duration_min: float, price: float) -> Dict:
        """
        Estimate market impact of an order.
        
        Args:
            order_size: in base currency (e.g., BTC)
            market_volume: avg volume per minute
            duration_min: execution window
            price: current market price
        """
        if market_volume <= 0 or duration_min <= 0:
            return {'total_bps': 0, 'temp_bps': 0, 'perm_bps': 0, 'cost_usd': 0}
        
        v = order_size / duration_min  # Execution rate
        participation = v / market_volume  # Participation rate
        
        # Temporary impact (from trading pressure, mean-reverts)
        temp = self.eta * participation ** 0.6
        
        # Permanent impact (information leakage, doesn't revert)
        perm = self.gamma * (order_size / (market_volume * duration_min)) ** 0.5
        
        total = temp + perm
        
        return {
            'total_bps': round(total * 10000, 2),
            'temp_bps': round(temp * 10000, 2),
            'perm_bps': round(perm * 10000, 2),
            'cost_usd': round(total * order_size * price, 4),
            'participation_rate': round(participation * 100, 2),
        }


# ═══════════════════════════════════════════════════════════════
# Section 2: TWAP Algorithm
# ═══════════════════════════════════════════════════════════════

@dataclass
class ExecutionSlice:
    """A single child order in an execution schedule."""
    slice_num: int
    time_offset_sec: int
    quantity: float
    expected_price: float
    actual_price: float = 0
    fill_time: float = 0
    slippage_bps: float = 0
    status: str = 'PENDING'


class TWAPAlgorithm:
    """
    Time-Weighted Average Price.
    Split order into equal-sized slices at equal time intervals.
    
    Pros: Predictable, low market impact for small orders
    Cons: Ignores volume patterns, can be gamed by HFT
    """
    
    def __init__(self, num_slices: int = 10, randomize: bool = True):
        self.num_slices = num_slices
        self.randomize = randomize
    
    def generate_schedule(self, total_qty: float, duration_sec: int,
                          start_price: float) -> List[ExecutionSlice]:
        """Generate TWAP execution schedule."""
        interval = duration_sec / self.num_slices
        qty_per_slice = total_qty / self.num_slices
        
        slices = []
        for i in range(self.num_slices):
            offset = int(i * interval)
            
            # Add ±10% randomization to avoid predictability
            if self.randomize and i > 0:
                jitter = int(interval * 0.1 * (2 * np.random.random() - 1))
                offset += jitter
            
            slices.append(ExecutionSlice(
                slice_num=i + 1,
                time_offset_sec=offset,
                quantity=round(qty_per_slice, 8),
                expected_price=start_price,
            ))
        
        return slices


# ═══════════════════════════════════════════════════════════════
# Section 3: VWAP Algorithm
# ═══════════════════════════════════════════════════════════════

class VWAPAlgorithm:
    """
    Volume-Weighted Average Price.
    Execute proportionally to historical volume profile.
    
    Pros: Matches market rhythm, lower impact than TWAP
    Cons: Volume profile may not match today's volume
    """
    
    def generate_schedule(self, total_qty: float, volume_profile: np.ndarray,
                          duration_sec: int, start_price: float) -> List[ExecutionSlice]:
        """
        Generate VWAP schedule based on historical volume profile.
        
        Args:
            volume_profile: array of relative volumes per period
        """
        # Normalize volume profile to sum to 1
        total_vol = np.sum(volume_profile)
        if total_vol <= 0:
            # Fall back to TWAP
            weights = np.ones(len(volume_profile)) / len(volume_profile)
        else:
            weights = volume_profile / total_vol
        
        n = len(weights)
        interval = duration_sec / n
        
        slices = []
        for i in range(n):
            qty = total_qty * weights[i]
            if qty < 1e-8:
                continue
            
            slices.append(ExecutionSlice(
                slice_num=i + 1,
                time_offset_sec=int(i * interval),
                quantity=round(qty, 8),
                expected_price=start_price,
            ))
        
        return slices
    
    @staticmethod
    def get_volume_profile(symbol: str, interval: str = '1h', days: int = 7) -> np.ndarray:
        """Fetch historical volume profile from Binance."""
        try:
            resp = requests.get('https://api.binance.com/api/v3/klines', params={
                'symbol': symbol, 'interval': interval, 'limit': min(days * 24, 500)
            }, timeout=10)
            if resp.status_code == 200:
                vols = [float(k[5]) for k in resp.json()]
                return np.array(vols[-24:])  # Last 24 periods
        except:
            pass
        return np.ones(24)  # Fallback uniform


# ═══════════════════════════════════════════════════════════════
# Section 4: Iceberg Algorithm
# ═══════════════════════════════════════════════════════════════

class IcebergAlgorithm:
    """
    Iceberg order: show only a small visible portion.
    When visible slice fills, place next slice.
    
    Pros: Hides true order size, prevents front-running
    Cons: Slower execution, may miss fast-moving markets
    """
    
    def __init__(self, show_pct: float = 0.10, variance: float = 0.20):
        """
        Args:
            show_pct: Fraction of total order visible at once
            variance: ± randomization of visible size (anti-detection)
        """
        self.show_pct = show_pct
        self.variance = variance
    
    def generate_schedule(self, total_qty: float, start_price: float) -> List[ExecutionSlice]:
        """Generate iceberg slices."""
        remaining = total_qty
        slices = []
        i = 0
        
        while remaining > 1e-8:
            base_size = total_qty * self.show_pct
            # Randomize size to avoid pattern detection
            random_factor = 1 + self.variance * (2 * np.random.random() - 1)
            show_size = min(base_size * random_factor, remaining)
            
            slices.append(ExecutionSlice(
                slice_num=i + 1,
                time_offset_sec=0,  # Triggered by fills, not time
                quantity=round(show_size, 8),
                expected_price=start_price,
            ))
            
            remaining -= show_size
            i += 1
        
        return slices


# ═══════════════════════════════════════════════════════════════
# Section 5: Implementation Shortfall
# ═══════════════════════════════════════════════════════════════

class ImplementationShortfall:
    """
    Balance urgency vs market impact.
    
    Low urgency → spread execution over time (like TWAP)
    High urgency → execute fast (accept higher impact)
    
    Optimal trajectory minimizes:
        E[cost] + λ × Var[cost]
    where λ = risk aversion (urgency)
    """
    
    def __init__(self, impact_model: MarketImpactModel = None):
        self.impact = impact_model or MarketImpactModel()
    
    def optimal_schedule(self, total_qty: float, duration_sec: int,
                          urgency: float, price: float,
                          market_vol_per_min: float) -> List[ExecutionSlice]:
        """
        Generate optimal execution schedule.
        
        Args:
            urgency: 0 (patient) to 1 (immediate)
        """
        # Higher urgency → fewer, larger slices
        # Lower urgency → more, smaller slices
        n_slices = max(2, int(20 * (1 - urgency) + 2))
        
        # Urgency skews schedule: front-load for high urgency
        if urgency > 0.7:
            # Exponential decay: execute most early
            weights = np.exp(-np.arange(n_slices) * urgency)
        elif urgency > 0.3:
            # Slightly front-loaded
            weights = np.linspace(1 + urgency, 1 - urgency, n_slices)
            weights = np.maximum(weights, 0.1)
        else:
            # Even (TWAP-like)
            weights = np.ones(n_slices)
        
        weights /= np.sum(weights)
        interval = duration_sec / n_slices
        
        slices = []
        for i in range(n_slices):
            qty = total_qty * weights[i]
            slices.append(ExecutionSlice(
                slice_num=i + 1,
                time_offset_sec=int(i * interval),
                quantity=round(qty, 8),
                expected_price=price,
            ))
        
        # Estimate costs
        est = self.impact.estimate_impact(total_qty, market_vol_per_min,
                                           duration_sec / 60, price)
        
        return slices, est


# ═══════════════════════════════════════════════════════════════
# Section 6: Slippage Tracker
# ═══════════════════════════════════════════════════════════════

@dataclass
class ExecutionRecord:
    """Record of a completed execution."""
    timestamp: str
    symbol: str
    direction: str
    algo: str
    signal_price: float         # Price when signal fired
    decision_price: float       # Price when order placed
    avg_fill_price: float       # Volume-weighted avg fill
    total_qty: float
    total_slices: int
    filled_slices: int
    duration_sec: int
    # Costs
    slippage_bps: float         # vs signal price
    market_impact_bps: float    # vs decision price
    commission_bps: float
    total_cost_bps: float
    # Quality
    arrival_cost_bps: float     # vs arrival (first slice) price
    vwap_deviation_bps: float   # vs market VWAP during execution


class SlippageTracker:
    """Track and analyze execution quality over time."""
    
    def __init__(self):
        self.records: List[ExecutionRecord] = []
    
    def record(self, signal_price: float, decision_price: float,
               fills: List[Dict], symbol: str, direction: str,
               algo: str = 'MARKET') -> ExecutionRecord:
        """
        Record execution and compute costs.
        
        fills: list of {'price': float, 'qty': float, 'time': float}
        """
        if not fills:
            return None
        
        # VWAP of fills
        total_qty = sum(f['qty'] for f in fills)
        avg_fill = sum(f['price'] * f['qty'] for f in fills) / total_qty if total_qty > 0 else decision_price
        
        # Slippage vs signal
        if direction == 'LONG':
            slippage = (avg_fill - signal_price) / signal_price * 10000
            impact = (avg_fill - decision_price) / decision_price * 10000
        else:
            slippage = (signal_price - avg_fill) / signal_price * 10000
            impact = (decision_price - avg_fill) / decision_price * 10000
        
        commission = 4  # ~4 bps round trip on Binance
        
        record = ExecutionRecord(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            direction=direction,
            algo=algo,
            signal_price=signal_price,
            decision_price=decision_price,
            avg_fill_price=round(avg_fill, 8),
            total_qty=total_qty,
            total_slices=len(fills),
            filled_slices=len(fills),
            duration_sec=int(fills[-1].get('time', 0) - fills[0].get('time', 0)) if len(fills) > 1 else 0,
            slippage_bps=round(slippage, 2),
            market_impact_bps=round(impact, 2),
            commission_bps=commission,
            total_cost_bps=round(slippage + commission, 2),
            arrival_cost_bps=round(slippage, 2),  # Simplified
            vwap_deviation_bps=0,  # Would need market VWAP
        )
        
        self.records.append(record)
        return record
    
    def summary(self) -> Dict:
        """Aggregate execution quality metrics."""
        if not self.records:
            return {'total_executions': 0}
        
        slippages = [r.slippage_bps for r in self.records]
        costs = [r.total_cost_bps for r in self.records]
        
        return {
            'total_executions': len(self.records),
            'avg_slippage_bps': round(np.mean(slippages), 2),
            'median_slippage_bps': round(np.median(slippages), 2),
            'p95_slippage_bps': round(np.percentile(slippages, 95), 2),
            'avg_total_cost_bps': round(np.mean(costs), 2),
            'worst_slippage_bps': round(max(slippages), 2),
            'best_slippage_bps': round(min(slippages), 2),
            'positive_slippage_pct': round(sum(1 for s in slippages if s < 0) / len(slippages) * 100, 1),
        }


# ═══════════════════════════════════════════════════════════════
# Section 7: Pre-Trade Cost Estimator
# ═══════════════════════════════════════════════════════════════

class PreTradeCostEstimator:
    """Estimate total cost before placing an order."""
    
    def __init__(self, impact_model: MarketImpactModel = None):
        self.impact = impact_model or MarketImpactModel()
    
    def estimate(self, symbol: str, qty: float, direction: str,
                  duration_min: float = 5, leverage: int = 10) -> Dict:
        """
        Pre-trade cost breakdown.
        """
        # Fetch current market data
        try:
            r = requests.get('https://api.binance.com/api/v3/ticker/24hr',
                            params={'symbol': symbol}, timeout=5)
            data = r.json()
            price = float(data['lastPrice'])
            volume_24h = float(data['volume'])
            vol_per_min = volume_24h / (24 * 60)
            spread = (float(data['askPrice']) - float(data['bidPrice'])) / price * 10000
        except:
            return {'error': 'Failed to fetch market data'}
        
        # Notional value
        notional = qty * price * leverage
        
        # 1. Spread cost (half spread, one way)
        spread_cost = spread / 2
        
        # 2. Commission
        commission = 4  # bps for maker/taker
        
        # 3. Market impact
        impact = self.impact.estimate_impact(qty, vol_per_min, duration_min, price)
        
        # 4. Slippage estimate (historical average + current volatility)
        slippage_est = max(1, spread)  # At least 1 bps slippage
        
        total = spread_cost + commission + impact['total_bps'] + slippage_est
        
        return {
            'symbol': symbol,
            'direction': direction,
            'quantity': qty,
            'price': price,
            'notional': round(notional, 2),
            'leverage': leverage,
            'costs_bps': {
                'spread': round(spread_cost, 2),
                'commission': commission,
                'market_impact': impact['total_bps'],
                'slippage_est': round(slippage_est, 2),
                'total': round(total, 2),
            },
            'costs_usd': {
                'total': round(total / 10000 * notional, 4),
            },
            'participation_rate': impact['participation_rate'],
            'recommendation': 'TWAP' if impact['participation_rate'] > 5 else 'MARKET',
        }


# ═══════════════════════════════════════════════════════════════
# Section 8: Simulation Engine
# ═══════════════════════════════════════════════════════════════

class ExecutionSimulator:
    """Simulate execution algorithms on historical data."""
    
    def simulate(self, symbol: str, qty: float, direction: str,
                  algo: str = 'twap', duration_min: int = 5) -> Dict:
        """Run execution simulation using recent kline data as price feed."""
        
        # Fetch 5m klines for simulation
        try:
            resp = requests.get('https://api.binance.com/api/v3/klines', params={
                'symbol': symbol, 'interval': '1m', 'limit': max(duration_min + 5, 30)
            }, timeout=10)
            klines = resp.json()
            prices = [float(k[4]) for k in klines]  # close prices
            volumes = [float(k[5]) for k in klines]
        except:
            return {'error': 'Failed to fetch data'}
        
        start_price = prices[0]
        
        # Generate schedule based on algo
        if algo == 'twap':
            engine = TWAPAlgorithm(num_slices=min(duration_min, 10))
            slices = engine.generate_schedule(qty, duration_min * 60, start_price)
        elif algo == 'vwap':
            engine = VWAPAlgorithm()
            vol_profile = np.array(volumes[:duration_min])
            slices = engine.generate_schedule(qty, vol_profile, duration_min * 60, start_price)
        elif algo == 'iceberg':
            engine = IcebergAlgorithm(show_pct=0.15)
            slices = engine.generate_schedule(qty, start_price)
        elif algo == 'is':
            engine = ImplementationShortfall()
            vol_per_min = np.mean(volumes)
            slices, est = engine.optimal_schedule(qty, duration_min * 60, 0.5, start_price, vol_per_min)
        else:
            return {'error': f'Unknown algo: {algo}'}
        
        # Simulate fills using price series
        fills = []
        total_cost = 0
        
        for i, s in enumerate(slices):
            # Use actual price at this time offset
            price_idx = min(i, len(prices) - 1)
            fill_price = prices[price_idx]
            
            # Add realistic slippage
            slippage = fill_price * 0.0002 * (1 if direction == 'LONG' else -1)
            fill_price += slippage
            
            s.actual_price = fill_price
            s.slippage_bps = (fill_price - s.expected_price) / s.expected_price * 10000
            if direction == 'SHORT':
                s.slippage_bps = -s.slippage_bps
            s.status = 'FILLED'
            
            fills.append({'price': fill_price, 'qty': s.quantity, 'time': i * 60})
        
        # Compute stats
        avg_fill = sum(f['price'] * f['qty'] for f in fills) / sum(f['qty'] for f in fills)
        
        if direction == 'LONG':
            total_slip = (avg_fill - start_price) / start_price * 10000
        else:
            total_slip = (start_price - avg_fill) / start_price * 10000
        
        # Compare with market order (single fill at start)
        market_slip = 2  # ~2 bps for instant market order
        
        # Compare with end price (opportunity cost)
        end_price = prices[-1]
        if direction == 'LONG':
            opp_cost = (end_price - avg_fill) / avg_fill * 10000
        else:
            opp_cost = (avg_fill - end_price) / avg_fill * 10000
        
        return {
            'algo': algo.upper(),
            'symbol': symbol,
            'direction': direction,
            'total_qty': qty,
            'start_price': start_price,
            'end_price': end_price,
            'avg_fill': round(avg_fill, 2),
            'slices': len(slices),
            'filled': sum(1 for s in slices if s.status == 'FILLED'),
            'duration_min': duration_min,
            'total_slippage_bps': round(total_slip, 2),
            'vs_market_order_bps': round(total_slip - market_slip, 2),
            'opportunity_cost_bps': round(opp_cost, 2),
            'slices_detail': [
                {'#': s.slice_num, 'qty': s.quantity, 'expected': round(s.expected_price, 2),
                 'actual': round(s.actual_price, 2), 'slip_bps': round(s.slippage_bps, 2)}
                for s in slices
            ],
        }


# ═══════════════════════════════════════════════════════════════
# Section 9: Report
# ═══════════════════════════════════════════════════════════════

def generate_report(results: Dict):
    print("\n" + "=" * 70)
    print(f"  NOOGH EXECUTION SIMULATION — {results.get('algo', '?')}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    print(f"\n📋 ORDER DETAILS")
    print(f"  {'Symbol:':<25} {results['symbol']}")
    print(f"  {'Direction:':<25} {results['direction']}")
    print(f"  {'Total Quantity:':<25} {results['total_qty']}")
    print(f"  {'Algorithm:':<25} {results['algo']}")
    print(f"  {'Duration:':<25} {results['duration_min']} min")
    
    print(f"\n💰 EXECUTION QUALITY")
    print(f"  {'Start Price:':<25} ${results['start_price']:,.2f}")
    print(f"  {'Avg Fill Price:':<25} ${results['avg_fill']:,.2f}")
    print(f"  {'End Price:':<25} ${results['end_price']:,.2f}")
    print(f"  {'Slices:':<25} {results['filled']}/{results['slices']}")
    print(f"  {'Total Slippage:':<25} {results['total_slippage_bps']:+.2f} bps")
    print(f"  {'vs Market Order:':<25} {results['vs_market_order_bps']:+.2f} bps")
    print(f"  {'Opp. Cost (timing):':<25} {results['opportunity_cost_bps']:+.2f} bps")
    
    print(f"\n📊 SLICE DETAIL")
    print(f"  {'#':<4} {'Qty':<12} {'Expected':<12} {'Actual':<12} {'Slip(bps)':<10}")
    print(f"  {'-'*50}")
    for s in results['slices_detail']:
        print(f"  {s['#']:<4} {s['qty']:<12.6f} ${s['expected']:<10,.2f} ${s['actual']:<10,.2f} {s['slip_bps']:+.2f}")
    
    total_bps = results['total_slippage_bps']
    print(f"\n🎯 VERDICT:")
    if abs(total_bps) < 2:
        print(f"  🟢 EXCELLENT — minimal slippage ({total_bps:+.2f} bps)")
    elif abs(total_bps) < 5:
        print(f"  🟡 ACCEPTABLE — moderate slippage ({total_bps:+.2f} bps)")
    else:
        print(f"  🔴 POOR — high slippage ({total_bps:+.2f} bps)")
    
    print(f"\n" + "=" * 70)


def run_comparison(symbol: str, qty: float, direction: str, duration: int):
    """Compare all algorithms side by side."""
    sim = ExecutionSimulator()
    algos = ['twap', 'vwap', 'iceberg', 'is']
    
    print(f"\n{'=' * 70}")
    print(f"  ALGORITHM COMPARISON — {symbol} {direction} {qty}")
    print(f"{'=' * 70}")
    print(f"\n{'Algo':<12} {'Slices':<8} {'Slip(bps)':<12} {'vs Mkt':<12} {'OppCost':<12}")
    print(f"{'-' * 56}")
    
    results = []
    for algo in algos:
        r = sim.simulate(symbol, qty, direction, algo, duration)
        if 'error' not in r:
            results.append(r)
            print(f"{r['algo']:<12} {r['filled']:<8} {r['total_slippage_bps']:>+8.2f}    {r['vs_market_order_bps']:>+8.2f}    {r['opportunity_cost_bps']:>+8.2f}")
    
    if results:
        best = min(results, key=lambda r: abs(r['total_slippage_bps']))
        print(f"\n  👑 Best: {best['algo']} ({best['total_slippage_bps']:+.2f} bps)")
    
    print(f"{'=' * 70}")
    return results


# ═══════════════════════════════════════════════════════════════
# Section 10: Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='NOOGH Execution Engine')
    parser.add_argument('command', choices=['simulate', 'compare', 'cost', 'analyze'])
    parser.add_argument('--symbol', default='BTCUSDT')
    parser.add_argument('--size', type=float, default=0.001, help='Order size in base currency')
    parser.add_argument('--direction', default='LONG', choices=['LONG', 'SHORT'])
    parser.add_argument('--algo', default='twap', choices=['twap', 'vwap', 'iceberg', 'is'])
    parser.add_argument('--duration', type=int, default=5, help='Execution window (minutes)')
    parser.add_argument('--leverage', type=int, default=10)
    args = parser.parse_args()
    
    if args.command == 'simulate':
        sim = ExecutionSimulator()
        result = sim.simulate(args.symbol, args.size, args.direction, args.algo, args.duration)
        if 'error' in result:
            logger.error(result['error'])
        else:
            generate_report(result)
    
    elif args.command == 'compare':
        run_comparison(args.symbol, args.size, args.direction, args.duration)
    
    elif args.command == 'cost':
        estimator = PreTradeCostEstimator()
        est = estimator.estimate(args.symbol, args.size, args.direction,
                                  args.duration, args.leverage)
        print(f"\n{'=' * 50}")
        print(f"  PRE-TRADE COST ESTIMATE — {args.symbol}")
        print(f"{'=' * 50}")
        print(f"  Notional: ${est['notional']:,.2f}")
        print(f"  Costs (bps):")
        for k, v in est['costs_bps'].items():
            print(f"    {k:<20} {v:>8.2f}")
        print(f"  Total USD: ${est['costs_usd']['total']:.4f}")
        print(f"  Recommendation: {est['recommendation']}")
        print(f"{'=' * 50}")
    
    elif args.command == 'analyze':
        logger.info("No historical executions yet. Run some trades first.")


if __name__ == '__main__':
    main()
