#!/usr/bin/env python3
"""
NOOGH Portfolio Optimization Engine
======================================
Man Group-style portfolio construction for crypto multi-asset allocation.

Methods:
- Mean-Variance (Markowitz)
- Risk Parity (Equal Risk Contribution)
- Hierarchical Risk Parity (HRP – Lopez de Prado)
- Minimum Variance
- Maximum Sharpe
- Scenario Analysis

Usage:
    python3 portfolio_optimizer.py --days 90
    python3 portfolio_optimizer.py --days 60 --method all
"""

import sys
import time
import json
import argparse
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

import numpy as np
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')

ASSETS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'AVAXUSDT', 'DOGEUSDT']


# ═══════════════════════════════════════════════════════════════
# Section 1: Data
# ═══════════════════════════════════════════════════════════════

def fetch_returns(symbols: List[str], interval: str = '1d', days: int = 90) -> Tuple[np.ndarray, List[str]]:
    """Fetch historical returns for all assets."""
    BASE = "https://api.binance.com/api/v3"
    all_returns = {}
    min_len = float('inf')
    
    logger.info(f"📊 Downloading {len(symbols)} assets ({days}d)...")
    for sym in symbols:
        try:
            r = requests.get(f"{BASE}/klines", params={
                'symbol': sym, 'interval': interval,
                'limit': min(days + 5, 500)
            }, timeout=10)
            if r.status_code == 200:
                closes = np.array([float(k[4]) for k in r.json()])
                returns = np.diff(closes) / closes[:-1]
                all_returns[sym] = returns
                min_len = min(min_len, len(returns))
        except Exception as e:
            logger.warning(f"⚠️ {sym}: {e}")
        time.sleep(0.1)
    
    # Align
    names = list(all_returns.keys())
    R = np.column_stack([all_returns[s][-int(min_len):] for s in names])
    logger.info(f"✅ {len(names)} assets, {R.shape[0]} periods")
    return R, names


# ═══════════════════════════════════════════════════════════════
# Section 2: Mean-Variance (Markowitz)
# ═══════════════════════════════════════════════════════════════

class MeanVarianceOptimizer:
    """
    Classic Markowitz mean-variance optimization.
    
    Maximize: w'μ - (λ/2) × w'Σw
    Subject to: Σw = 1, w >= 0
    
    Solved via Monte Carlo + gradient refinement.
    """
    
    def __init__(self, risk_aversion: float = 2.0):
        self.risk_aversion = risk_aversion
    
    def optimize(self, mu: np.ndarray, cov: np.ndarray,
                  n_portfolios: int = 10000) -> Dict:
        """Find optimal portfolio via simulation."""
        n = len(mu)
        
        best_sharpe = -np.inf
        best_w = np.ones(n) / n
        
        all_returns = []
        all_risks = []
        all_weights = []
        
        for _ in range(n_portfolios):
            w = np.random.dirichlet(np.ones(n))
            
            port_ret = w @ mu
            port_risk = np.sqrt(w @ cov @ w)
            sharpe = port_ret / port_risk if port_risk > 0 else 0
            
            all_returns.append(port_ret)
            all_risks.append(port_risk)
            all_weights.append(w)
            
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_w = w.copy()
        
        # Minimum variance portfolio
        min_var_idx = np.argmin(all_risks)
        min_var_w = all_weights[min_var_idx]
        
        return {
            'max_sharpe': {
                'weights': np.round(best_w, 4),
                'return': round(best_w @ mu * 252 * 100, 2),
                'risk': round(np.sqrt(best_w @ cov @ best_w) * np.sqrt(252) * 100, 2),
                'sharpe': round(best_sharpe * np.sqrt(252), 2),
            },
            'min_variance': {
                'weights': np.round(min_var_w, 4),
                'return': round(min_var_w @ mu * 252 * 100, 2),
                'risk': round(np.sqrt(min_var_w @ cov @ min_var_w) * np.sqrt(252) * 100, 2),
            },
            'frontier': {
                'returns': [r * 252 * 100 for r in all_returns],
                'risks': [r * np.sqrt(252) * 100 for r in all_risks],
            }
        }


# ═══════════════════════════════════════════════════════════════
# Section 3: Risk Parity
# ═══════════════════════════════════════════════════════════════

class RiskParityOptimizer:
    """
    Equal Risk Contribution (ERC / Risk Parity).
    
    Each asset contributes equally to portfolio risk:
        RC_i = w_i × (Σw)_i / σ_p
    
    Solved iteratively.
    """
    
    def optimize(self, cov: np.ndarray, target_risk: List[float] = None,
                  max_iter: int = 1000, tol: float = 1e-8) -> Dict:
        n = len(cov)
        budget = np.ones(n) / n if target_risk is None else np.array(target_risk)
        budget /= np.sum(budget)
        
        w = np.ones(n) / n
        
        for _ in range(max_iter):
            sigma = np.sqrt(w @ cov @ w)
            if sigma == 0:
                break
            
            # Marginal risk contribution
            mrc = cov @ w / sigma
            
            # Risk contribution
            rc = w * mrc
            
            # Target risk contribution
            target_rc = budget * sigma
            
            # Update weights
            w_new = w * target_rc / rc
            w_new[w_new < 0] = 0
            w_new /= np.sum(w_new)
            
            if np.max(np.abs(w_new - w)) < tol:
                break
            w = w_new
        
        sigma = np.sqrt(w @ cov @ w)
        rc = w * (cov @ w) / sigma if sigma > 0 else np.zeros(n)
        
        return {
            'weights': np.round(w, 4),
            'risk_contributions': np.round(rc / np.sum(rc) * 100, 1) if np.sum(rc) > 0 else np.zeros(n),
            'portfolio_risk': round(sigma * np.sqrt(252) * 100, 2),
        }


# ═══════════════════════════════════════════════════════════════
# Section 4: Hierarchical Risk Parity (HRP)
# ═══════════════════════════════════════════════════════════════

class HRPOptimizer:
    """
    Hierarchical Risk Parity (Lopez de Prado).
    
    1. Tree clustering on correlation matrix
    2. Quasi-diagonalize covariance matrix
    3. Recursive bisection for allocation
    
    Advantage: no covariance matrix inversion → more stable.
    """
    
    def optimize(self, returns: np.ndarray, names: List[str]) -> Dict:
        cov = np.cov(returns.T)
        corr = np.corrcoef(returns.T)
        n = len(names)
        
        # 1. Clustering via single-linkage on distance matrix
        dist = np.sqrt(0.5 * (1 - corr))
        np.fill_diagonal(dist, 0)
        
        order = self._seriation(dist, n)
        
        # 2. Recursive bisection
        w = self._recursive_bisection(cov, order)
        
        sigma = np.sqrt(w @ cov @ w)
        
        return {
            'weights': np.round(w, 4),
            'cluster_order': [names[i] for i in order],
            'portfolio_risk': round(sigma * np.sqrt(252) * 100, 2),
        }
    
    def _seriation(self, dist: np.ndarray, n: int) -> List[int]:
        """Simple agglomerative clustering → seriation order."""
        # Track which items are in each cluster
        clusters = {i: [i] for i in range(n)}
        active = set(range(n))
        next_id = n
        
        link_order = []
        
        while len(active) > 1:
            # Find closest pair
            best_d = float('inf')
            best_i, best_j = -1, -1
            active_list = sorted(active)
            
            for ii in range(len(active_list)):
                for jj in range(ii + 1, len(active_list)):
                    ci, cj = active_list[ii], active_list[jj]
                    # Average linkage
                    d = np.mean([dist[a][b] for a in clusters[ci] for b in clusters[cj]])
                    if d < best_d:
                        best_d = d
                        best_i, best_j = ci, cj
            
            # Merge
            merged = clusters[best_i] + clusters[best_j]
            clusters[next_id] = merged
            active.discard(best_i)
            active.discard(best_j)
            active.add(next_id)
            link_order.append((best_i, best_j, next_id))
            next_id += 1
        
        # Get leaf order from final cluster
        final = list(active)[0]
        return clusters[final]
    
    def _recursive_bisection(self, cov: np.ndarray, order: List[int]) -> np.ndarray:
        """Allocate weights via recursive bisection."""
        n = cov.shape[0]
        w = np.ones(n)
        
        items = [order]
        
        while items:
            new_items = []
            for subset in items:
                if len(subset) <= 1:
                    continue
                mid = len(subset) // 2
                left = subset[:mid]
                right = subset[mid:]
                
                # Variance of each half
                var_left = self._cluster_var(cov, left)
                var_right = self._cluster_var(cov, right)
                
                # Allocate inversely proportional to variance
                total = var_left + var_right
                if total > 0:
                    alpha = 1 - var_left / total
                else:
                    alpha = 0.5
                
                for i in left:
                    w[i] *= alpha
                for i in right:
                    w[i] *= (1 - alpha)
                
                if len(left) > 1:
                    new_items.append(left)
                if len(right) > 1:
                    new_items.append(right)
            
            items = new_items
        
        w /= np.sum(w)
        return w
    
    def _cluster_var(self, cov, indices):
        """Variance of equal-weight portfolio of indices."""
        n = len(indices)
        if n == 0: return 0
        w = np.zeros(cov.shape[0])
        w[indices] = 1.0 / n
        return w @ cov @ w


# ═══════════════════════════════════════════════════════════════
# Section 5: Constraint Framework
# ═══════════════════════════════════════════════════════════════

@dataclass
class Constraints:
    min_weight: float = 0.0      # Long-only
    max_weight: float = 0.40     # Max 40% in single asset
    max_turnover: float = 0.30   # Max 30% turnover per rebalance
    min_assets: int = 3          # Minimum diversification
    
    def apply(self, weights: np.ndarray, current_weights: np.ndarray = None) -> np.ndarray:
        """Apply constraints to proposed weights."""
        w = weights.copy()
        
        # Long only
        w = np.maximum(w, self.min_weight)
        
        # Max weight cap
        w = np.minimum(w, self.max_weight)
        
        # Re-normalize
        if np.sum(w) > 0:
            w /= np.sum(w)
        
        # Turnover constraint
        if current_weights is not None:
            turnover = np.sum(np.abs(w - current_weights))
            if turnover > self.max_turnover:
                # Blend toward target
                blend = self.max_turnover / turnover
                w = current_weights + blend * (w - current_weights)
                w = np.maximum(w, 0)
                w /= np.sum(w)
        
        # Min assets
        nonzero = np.sum(w > 0.01)
        if nonzero < self.min_assets:
            # Add equal weight to smallest assets
            zero_idx = np.argsort(w)[:self.min_assets - int(nonzero)]
            for idx in zero_idx:
                w[idx] = 0.05
            w /= np.sum(w)
        
        return w


# ═══════════════════════════════════════════════════════════════
# Section 6: Performance Attribution
# ═══════════════════════════════════════════════════════════════

class PerformanceAttribution:
    """Brinson-style performance attribution."""
    
    @staticmethod
    def attribute(portfolio_weights: np.ndarray, benchmark_weights: np.ndarray,
                  portfolio_returns: np.ndarray, benchmark_returns: np.ndarray,
                  names: List[str]) -> Dict:
        """
        Decompose active return into:
        - Allocation effect: overweighting winning sectors
        - Selection effect: picking better assets within sectors
        - Interaction: combined effect
        """
        n = len(names)
        
        # Active weights
        active_w = portfolio_weights - benchmark_weights
        
        # Returns
        port_ret = portfolio_weights @ portfolio_returns
        bench_ret = benchmark_weights @ benchmark_returns
        active_ret = port_ret - bench_ret
        
        # Attribution
        allocation = active_w * (benchmark_returns - bench_ret)
        selection = benchmark_weights * (portfolio_returns - benchmark_returns)
        interaction = active_w * (portfolio_returns - benchmark_returns)
        
        return {
            'total_active_return': round(active_ret * 100, 4),
            'allocation_effect': round(np.sum(allocation) * 100, 4),
            'selection_effect': round(np.sum(selection) * 100, 4),
            'interaction_effect': round(np.sum(interaction) * 100, 4),
            'by_asset': {
                names[i]: {
                    'active_weight': round(active_w[i] * 100, 2),
                    'allocation': round(allocation[i] * 100, 4),
                    'selection': round(selection[i] * 100, 4),
                }
                for i in range(n)
            }
        }


# ═══════════════════════════════════════════════════════════════
# Section 7: Scenario Analysis
# ═══════════════════════════════════════════════════════════════

class ScenarioAnalysis:
    """Test portfolio under different market scenarios."""
    
    SCENARIOS = {
        'Bull Market': {'BTC': 0.30, 'ETH': 0.50, 'SOL': 0.80, 'BNB': 0.20,
                        'XRP': 0.40, 'ADA': 0.60, 'AVAX': 0.70, 'DOGE': 1.00},
        'Bear Market': {'BTC': -0.30, 'ETH': -0.45, 'SOL': -0.60, 'BNB': -0.25,
                        'XRP': -0.35, 'ADA': -0.50, 'AVAX': -0.55, 'DOGE': -0.70},
        'BTC Dominance': {'BTC': 0.20, 'ETH': -0.10, 'SOL': -0.15, 'BNB': -0.05,
                          'XRP': -0.20, 'ADA': -0.25, 'AVAX': -0.20, 'DOGE': -0.30},
        'Alt Season': {'BTC': 0.05, 'ETH': 0.30, 'SOL': 0.50, 'BNB': 0.15,
                       'XRP': 0.40, 'ADA': 0.45, 'AVAX': 0.55, 'DOGE': 0.80},
        'Flash Crash': {'BTC': -0.15, 'ETH': -0.25, 'SOL': -0.40, 'BNB': -0.20,
                        'XRP': -0.30, 'ADA': -0.35, 'AVAX': -0.45, 'DOGE': -0.50},
    }
    
    @classmethod
    def analyze(cls, weights: np.ndarray, names: List[str]) -> Dict:
        results = {}
        name_map = {n.replace('USDT', ''): i for i, n in enumerate(names)}
        
        for scenario, returns in cls.SCENARIOS.items():
            ret_vec = np.zeros(len(names))
            for asset, ret in returns.items():
                if asset in name_map:
                    ret_vec[name_map[asset]] = ret
            
            port_ret = weights @ ret_vec
            results[scenario] = round(port_ret * 100, 2)
        
        return results


# ═══════════════════════════════════════════════════════════════
# Section 8: Report
# ═══════════════════════════════════════════════════════════════

def generate_report(names: List[str], mu: np.ndarray, cov: np.ndarray,
                    mv_result: Dict, rp_result: Dict, hrp_result: Dict):
    
    print("\n" + "=" * 85)
    print(f"  NOOGH PORTFOLIO OPTIMIZATION — {len(names)} Crypto Assets")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')} | Man Group Framework")
    print("=" * 85)
    
    # Asset Stats
    print(f"\n📊 ASSET STATISTICS")
    print(f"  {'Asset':<12} {'Ann.Ret%':<12} {'Ann.Vol%':<12} {'Sharpe':<10}")
    print(f"  {'-'*46}")
    vols = np.sqrt(np.diag(cov)) * np.sqrt(252) * 100
    rets = mu * 252 * 100
    for i, name in enumerate(names):
        sr = rets[i] / vols[i] if vols[i] > 0 else 0
        print(f"  {name:<12} {rets[i]:>+8.1f}    {vols[i]:>8.1f}    {sr:>+6.2f}")
    
    # Correlation Matrix
    corr = np.corrcoef(mu)  # Simplified — use returns for real
    
    # Allocation Comparison
    print(f"\n{'─' * 85}")
    print(f"  ALLOCATION COMPARISON")
    print(f"{'─' * 85}")
    
    header = f"  {'Asset':<12}"
    for method in ['Max Sharpe', 'Risk Parity', 'HRP']:
        header += f" {method:<14}"
    print(header)
    print(f"  {'-'*54}")
    
    for i, name in enumerate(names):
        ms_w = mv_result['max_sharpe']['weights'][i] * 100
        rp_w = rp_result['weights'][i] * 100
        hrp_w = hrp_result['weights'][i] * 100
        print(f"  {name:<12} {ms_w:>10.1f}%    {rp_w:>10.1f}%    {hrp_w:>10.1f}%")
    
    # Risk metrics
    print(f"\n  {'Metric':<20} {'Max Sharpe':<14} {'Risk Parity':<14} {'HRP':<14}")
    print(f"  {'-'*62}")
    print(f"  {'Ann. Return':<20} {mv_result['max_sharpe']['return']:>10.1f}%    {'':14} {'':14}")
    print(f"  {'Ann. Risk':<20} {mv_result['max_sharpe']['risk']:>10.1f}%    {rp_result['portfolio_risk']:>10.1f}%    {hrp_result['portfolio_risk']:>10.1f}%")
    print(f"  {'Sharpe':<20} {mv_result['max_sharpe']['sharpe']:>10.2f}")
    
    # Risk Parity contributions
    print(f"\n📊 RISK PARITY — RISK CONTRIBUTIONS")
    for i, name in enumerate(names):
        bar = "█" * int(rp_result['risk_contributions'][i])
        print(f"  {name:<12} {rp_result['risk_contributions'][i]:>5.1f}%  {bar}")
    
    # Scenario Analysis
    print(f"\n🎬 SCENARIO ANALYSIS")
    scenarios_ms = ScenarioAnalysis.analyze(mv_result['max_sharpe']['weights'], names)
    scenarios_rp = ScenarioAnalysis.analyze(rp_result['weights'], names)
    scenarios_hrp = ScenarioAnalysis.analyze(hrp_result['weights'], names)
    
    print(f"  {'Scenario':<20} {'Max Sharpe':<14} {'Risk Parity':<14} {'HRP':<14}")
    print(f"  {'-'*62}")
    for scenario in ScenarioAnalysis.SCENARIOS:
        print(f"  {scenario:<20} {scenarios_ms[scenario]:>+8.1f}%     {scenarios_rp[scenario]:>+8.1f}%     {scenarios_hrp[scenario]:>+8.1f}%")
    
    # Recommendation
    print(f"\n{'═' * 85}")
    print(f"  🎯 RECOMMENDATION")
    print(f"{'═' * 85}")
    
    # Best method based on worst-case scenario
    worst_ms = min(scenarios_ms.values())
    worst_rp = min(scenarios_rp.values())
    worst_hrp = min(scenarios_hrp.values())
    
    best_worst = max(worst_ms, worst_rp, worst_hrp)
    if best_worst == worst_hrp:
        rec = 'HRP'
        rec_w = hrp_result['weights']
    elif best_worst == worst_rp:
        rec = 'Risk Parity'
        rec_w = rp_result['weights']
    else:
        rec = 'Max Sharpe'
        rec_w = mv_result['max_sharpe']['weights']
    
    print(f"  Best method (min worst-case): {rec}")
    print(f"  Worst-case scenario returns: MS={worst_ms:+.1f}%, RP={worst_rp:+.1f}%, HRP={worst_hrp:+.1f}%")
    print(f"\n  Recommended allocation:")
    for i, name in enumerate(names):
        if rec_w[i] > 0.01:
            bar = "█" * int(rec_w[i] * 50)
            print(f"    {name:<12} {rec_w[i]*100:>5.1f}%  {bar}")
    
    print(f"\n" + "=" * 85)


# ═══════════════════════════════════════════════════════════════
# Section 9: Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='NOOGH Portfolio Optimizer')
    parser.add_argument('--days', type=int, default=90)
    parser.add_argument('--interval', default='1d')
    parser.add_argument('--symbols', nargs='+', default=ASSETS)
    parser.add_argument('--method', default='all', choices=['all', 'markowitz', 'rp', 'hrp'])
    args = parser.parse_args()
    
    # Fetch data
    R, names = fetch_returns(args.symbols, args.interval, args.days)
    
    # Statistics
    mu = np.mean(R, axis=0)
    cov = np.cov(R.T)
    
    # 1. Mean-Variance
    logger.info("📐 Running Mean-Variance optimization...")
    mv = MeanVarianceOptimizer()
    mv_result = mv.optimize(mu, cov)
    
    # 2. Risk Parity
    logger.info("⚖️ Running Risk Parity...")
    rp = RiskParityOptimizer()
    rp_result = rp.optimize(cov)
    
    # 3. HRP
    logger.info("🌳 Running Hierarchical Risk Parity...")
    hrp = HRPOptimizer()
    hrp_result = hrp.optimize(R, names)
    
    # Apply constraints
    constraints = Constraints(max_weight=0.40, min_assets=3)
    mv_result['max_sharpe']['weights'] = constraints.apply(mv_result['max_sharpe']['weights'])
    rp_result['weights'] = constraints.apply(rp_result['weights'])
    hrp_result['weights'] = constraints.apply(hrp_result['weights'])
    
    # Report
    generate_report(names, mu, cov, mv_result, rp_result, hrp_result)


if __name__ == '__main__':
    main()
