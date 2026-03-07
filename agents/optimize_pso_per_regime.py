#!/usr/bin/env python3
"""
Phase 4.1: Multi-Regime PSO Optimization
=========================================
Optimizes separate policies for LOW/NORMAL/HIGH volatility regimes

Architecture:
- Layer B: Statistical Alpha Filter (always on)
- Layer C: Linear Score Policy with learnable weights (per regime)

Output:
- params_LOW.json
- params_NORMAL.json
- params_HIGH.json

Each with A/B/C window validation
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load Layer B filters
import importlib.util
filter_path = Path(__file__).parent.parent / 'strategies' / 'brain_improved_filters.py'
spec = importlib.util.spec_from_file_location("brain_improved_filters", filter_path)
filters_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(filters_module)
improved_long_filter = filters_module.improved_long_filter
improved_short_filter = filters_module.improved_short_filter


# ============================================================
# Feature Extraction & Normalization
# ============================================================

FEATURES = [
    'atr_pct',
    'vol_z',
    'taker_buy_ratio',
    'tbr_delta',
    'range_pct',
    'rsi_slope',
    'ema_trend_dir',
]

N_FEATURES = len(FEATURES)


def extract_features(setup: Dict) -> np.ndarray:
    """Extract feature vector from setup"""
    return np.array([
        setup.get('atr_pct', 0.0),
        setup.get('vol_z', 0.0),
        setup.get('taker_buy_ratio', 0.5),
        setup.get('tbr_delta', 0.0),
        setup.get('range_pct', 0.0),
        setup.get('rsi_slope', 0.0),
        setup.get('ema_trend_dir', 0.0),
    ], dtype=np.float32)


def statistical_alpha_filter(setup: Dict) -> Tuple[bool, str]:
    """Layer B filter (MUST ALWAYS BE ON)"""
    signal = setup.get('signal')
    if signal == 'LONG':
        return improved_long_filter(setup)
    elif signal == 'SHORT':
        return improved_short_filter(setup)
    else:
        return False, "Unknown signal"


# ============================================================
# Policy (Fixed Structure, Variable Parameters)
# ============================================================

@dataclass
class Policy:
    """
    Linear score policy with gate

    Parameters:
    - weights: [w1, w2, ..., w7] for features
    - threshold: T for decision boundary
    - gate_atr: X (reject if atr_pct > X)
    """
    weights: np.ndarray  # shape (7,)
    threshold: float
    gate_atr: float

    def __call__(self, features: np.ndarray) -> Tuple[bool, float]:
        """
        Evaluate policy on features

        Returns: (pass: bool, score: float)
        """
        # Gate check (simple hard filter)
        if features[0] > self.gate_atr:  # atr_pct
            return False, 0.0

        # Linear score
        score = np.dot(self.weights, features)

        # Decision
        passed = score > self.threshold

        return passed, score

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        return {
            'weights': self.weights.tolist(),
            'threshold': float(self.threshold),
            'gate_atr': float(self.gate_atr),
            'features': FEATURES,
        }


# ============================================================
# Evaluator (Layer B → Layer C → Metrics)
# ============================================================

class PolicyEvaluator:
    def __init__(self, setups: List[Dict]):
        self.setups = setups
        print(f"✅ Loaded {len(self.setups)} setups")

    def calculate_r_multiple(self, setup: Dict) -> Optional[float]:
        """Calculate R-multiple for a trade"""
        signal = setup.get('signal')
        outcome = setup.get('outcome')
        entry = setup.get('entry_price', 0)
        sl = setup.get('stop_loss', 0)
        tp = setup.get('take_profit', 0)

        if not all([signal, outcome, entry, sl, tp]):
            return None

        # Calculate risk (1R)
        if signal == 'LONG':
            risk = entry - sl
            if outcome == 'WIN':
                pnl = tp - entry
            else:
                pnl = sl - entry  # negative
        else:  # SHORT
            risk = sl - entry
            if outcome == 'WIN':
                pnl = entry - tp
            else:
                pnl = entry - sl  # negative

        if risk <= 0:
            return None

        r_multiple = pnl / risk
        return r_multiple

    def evaluate(
        self,
        policy: Policy,
        data: List[Dict],
        window_name: str = "ALL"
    ) -> Dict:
        """
        Evaluate policy on setups

        Returns metrics: {pf, dd, winrate, n_trades, total_r, ...}
        """
        trades = 0
        wins = 0
        losses = 0
        win_r = 0.0
        loss_r = 0.0
        total_r = 0.0

        equity = 100.0
        peak = equity
        max_dd = 0.0

        for setup in data:
            # Layer B filter
            ok_b, _ = statistical_alpha_filter(setup)
            if not ok_b:
                continue

            features = extract_features(setup)

            # Policy decision
            passed, score = policy(features)
            if not passed:
                continue

            # Calculate R
            r = self.calculate_r_multiple(setup)
            if r is None:
                continue

            trades += 1
            total_r += r

            if r > 0:
                wins += 1
                win_r += r
            else:
                losses += 1
                loss_r += abs(r)

            # Equity tracking
            equity += r
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        # Metrics
        winrate = (wins / trades * 100) if trades > 0 else 0
        pf = (win_r / loss_r) if loss_r > 0 else 0
        avg_win = (win_r / wins) if wins > 0 else 0
        avg_loss = (loss_r / losses) if losses > 0 else 0

        return {
            'window': window_name,
            'n_trades': trades,
            'wins': wins,
            'losses': losses,
            'winrate': winrate,
            'pf': pf,
            'total_r': total_r,
            'win_r': win_r,
            'loss_r': loss_r,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_dd': max_dd * 100,
            'final_equity': equity,
        }

    def fitness(
        self,
        policy: Policy,
        train_data: List[Dict],
        val_data: List[Dict],
        mode: str = "robust"
    ) -> float:
        """
        Calculate fitness score

        Modes:
        - "robust": 0.7*train + 0.3*val with stability penalty
        - "aggressive": train only
        """
        res_train = self.evaluate(policy, train_data, "TRAIN")
        res_val = self.evaluate(policy, val_data, "VAL")

        # Kill conditions
        if res_train['n_trades'] < 5:
            return 0.0
        if res_train['pf'] <= 1.0:
            return 0.0
        if res_train['max_dd'] > 30:
            return 0.0

        # Fitness components
        def score_single(res):
            # Normalize PF (cap at 3.0)
            pf_norm = min(res['pf'], 3.0) / 3.0

            # Expectancy
            exp = res['total_r'] / res['n_trades'] if res['n_trades'] > 0 else 0
            exp_norm = np.tanh(exp * 2)  # soft normalization

            # DD penalty
            dd_penalty = np.exp(-res['max_dd'] / 10)  # exponential decay

            # Trade count bonus (more is better, up to a point)
            n_bonus = min(res['n_trades'] / 30, 1.0)

            return (pf_norm * 0.4 + exp_norm * 0.3 + dd_penalty * 0.2 + n_bonus * 0.1)

        score_train = score_single(res_train)
        score_val = score_single(res_val) if res_val['n_trades'] > 0 else 0

        if mode == "robust":
            # Weighted + stability
            base = 0.7 * score_train + 0.3 * score_val
            stability = min(score_train, score_val) / max(score_train, score_val, 1e-9)
            return base * stability
        else:
            return score_train


# ============================================================
# PSO (Particle Swarm Optimization)
# ============================================================

class PSO:
    """
    Particle Swarm Optimization for Policy parameters

    Search space:
    - weights: [-2, 2] for each of 7 features
    - threshold: [-5, 5]
    - gate_atr: [0, 0.02]
    """

    def __init__(
        self,
        evaluator: PolicyEvaluator,
        train_data: List[Dict],
        val_data: List[Dict],
        n_particles: int = 30,
        max_iter: int = 50,
        w: float = 0.7,
        c1: float = 1.5,
        c2: float = 1.5,
    ):
        self.evaluator = evaluator
        self.train_data = train_data
        self.val_data = val_data
        self.n_particles = n_particles
        self.max_iter = max_iter
        self.w = w  # inertia
        self.c1 = c1  # cognitive
        self.c2 = c2  # social

        # Search space bounds
        self.dim = N_FEATURES + 2  # weights + threshold + gate_atr
        self.lb = np.array([-2.0] * N_FEATURES + [-5.0, 0.0])
        self.ub = np.array([2.0] * N_FEATURES + [5.0, 0.02])

        # Initialize swarm
        self.positions = np.random.uniform(
            self.lb, self.ub, (n_particles, self.dim)
        )
        self.velocities = np.random.uniform(
            -1, 1, (n_particles, self.dim)
        ) * (self.ub - self.lb) * 0.1

        self.pbest_pos = self.positions.copy()
        self.pbest_fit = np.zeros(n_particles)

        self.gbest_pos = None
        self.gbest_fit = 0.0

        self.history = []

    def params_to_policy(self, params: np.ndarray) -> Policy:
        """Convert parameter vector to Policy"""
        weights = params[:N_FEATURES]
        threshold = params[N_FEATURES]
        gate_atr = params[N_FEATURES + 1]
        return Policy(weights, threshold, gate_atr)

    def optimize(self) -> Tuple[Policy, float]:
        """Run PSO optimization"""
        # Initial evaluation
        for i in range(self.n_particles):
            policy = self.params_to_policy(self.positions[i])
            fit = self.evaluator.fitness(policy, self.train_data, self.val_data)
            self.pbest_fit[i] = fit

            if fit > self.gbest_fit:
                self.gbest_fit = fit
                self.gbest_pos = self.positions[i].copy()

        # Main loop
        for iter_num in range(self.max_iter):
            for i in range(self.n_particles):
                # Update velocity
                r1 = np.random.random(self.dim)
                r2 = np.random.random(self.dim)

                self.velocities[i] = (
                    self.w * self.velocities[i]
                    + self.c1 * r1 * (self.pbest_pos[i] - self.positions[i])
                    + self.c2 * r2 * (self.gbest_pos - self.positions[i])
                )

                # Update position
                self.positions[i] += self.velocities[i]

                # Clip to bounds
                self.positions[i] = np.clip(self.positions[i], self.lb, self.ub)

                # Evaluate
                policy = self.params_to_policy(self.positions[i])
                fit = self.evaluator.fitness(policy, self.train_data, self.val_data)

                # Update pbest
                if fit > self.pbest_fit[i]:
                    self.pbest_fit[i] = fit
                    self.pbest_pos[i] = self.positions[i].copy()

                # Update gbest
                if fit > self.gbest_fit:
                    self.gbest_fit = fit
                    self.gbest_pos = self.positions[i].copy()

            # Log progress
            if (iter_num + 1) % 10 == 0:
                avg_fit = np.mean(self.pbest_fit)
                print(f"   Iter {iter_num+1:3d}/{self.max_iter} | "
                      f"Best: {self.gbest_fit:.4f} | "
                      f"Avg: {avg_fit:.4f}")

            self.history.append({
                'iter': iter_num + 1,
                'gbest': self.gbest_fit,
                'avg': float(np.mean(self.pbest_fit)),
            })

        best_policy = self.params_to_policy(self.gbest_pos)
        return best_policy, self.gbest_fit


# ============================================================
# Multi-Regime Optimizer
# ============================================================

class MultiRegimeOptimizer:
    def __init__(self, data_file: Path):
        self.data_file = data_file
        self.all_setups = []
        self.regime_setups = {}
        self.load_data()

    def load_data(self):
        """Load all setups and split by regime"""
        if not self.data_file.exists():
            print(f"❌ Data file not found: {self.data_file}")
            return

        with open(self.data_file, 'r') as f:
            for line in f:
                self.all_setups.append(json.loads(line))

        # Sort by timestamp for temporal splits
        self.all_setups.sort(key=lambda x: x.get('timestamp', ''))

        print(f"\n{'='*70}")
        print(f"📊 DATA LOADING")
        print(f"{'='*70}")
        print(f"Total setups: {len(self.all_setups)}")

        # Split by regime
        for setup in self.all_setups:
            regime = setup.get('vol_regime', 'UNKNOWN')
            if regime not in self.regime_setups:
                self.regime_setups[regime] = []
            self.regime_setups[regime].append(setup)

        # Print regime distribution
        print(f"\n📈 Regime Distribution:")
        for regime, setups in sorted(self.regime_setups.items()):
            print(f"   {regime:10s}: {len(setups):4d} setups ({len(setups)/len(self.all_setups)*100:.1f}%)")

    def optimize_regime(
        self,
        regime: str,
        n_particles: int = 30,
        max_iter: int = 50
    ) -> Dict:
        """
        Optimize policy for a single regime

        Returns: {
            'regime': str,
            'policy': Policy,
            'fitness': float,
            'results': {A, B, ALL, C},
            'history': [...],
        }
        """
        setups = self.regime_setups.get(regime, [])

        if len(setups) < 20:
            print(f"❌ {regime}: Not enough data ({len(setups)} setups)")
            return None

        print(f"\n{'='*70}")
        print(f"🧬 PSO OPTIMIZATION - {regime} REGIME")
        print(f"{'='*70}")
        print(f"Total setups: {len(setups)}")

        # Split into A/B (70/30) for train/val
        split_idx = int(len(setups) * 0.7)
        train_data = setups[:split_idx]
        val_data = setups[split_idx:]

        print(f"Train (A): {len(train_data)} setups")
        print(f"Val (B): {len(val_data)} setups")
        print(f"Particles: {n_particles}")
        print(f"Max Iterations: {max_iter}")
        print(f"{'='*70}\n")

        # Initialize evaluator
        evaluator = PolicyEvaluator(setups)

        # Run PSO
        pso = PSO(
            evaluator,
            train_data,
            val_data,
            n_particles=n_particles,
            max_iter=max_iter,
        )

        best_policy, best_fitness = pso.optimize()

        print(f"\n✅ Optimization Complete!")
        print(f"🏆 Best Fitness: {best_fitness:.4f}\n")

        # Evaluate on all windows
        res_a = evaluator.evaluate(best_policy, train_data, "A")
        res_b = evaluator.evaluate(best_policy, val_data, "B")
        res_all = evaluator.evaluate(best_policy, setups, "ALL")

        # Window C: Temporal holdout (last 15% of ALL data)
        c_start = int(len(self.all_setups) * 0.85)
        window_c_all = self.all_setups[c_start:]
        window_c_regime = [s for s in window_c_all if s.get('vol_regime') == regime]
        res_c = evaluator.evaluate(best_policy, window_c_regime, "C") if window_c_regime else None

        return {
            'regime': regime,
            'policy': best_policy,
            'fitness': best_fitness,
            'results': {
                'A': res_a,
                'B': res_b,
                'ALL': res_all,
                'C': res_c,
            },
            'history': pso.history,
            'data_stats': {
                'total': len(setups),
                'train': len(train_data),
                'val': len(val_data),
                'window_c': len(window_c_regime) if window_c_regime else 0,
            }
        }

    def print_results(self, result: Dict):
        """Print formatted results for a regime"""
        regime = result['regime']
        policy = result['policy']
        results = result['results']

        print(f"\n{'='*70}")
        print(f"📊 {regime} REGIME - RESULTS")
        print(f"{'='*70}")

        print(f"\n🔧 Learned Parameters:")
        print(f"   Weights: {policy.weights}")
        print(f"   Threshold: {policy.threshold:.4f}")
        print(f"   Gate ATR: {policy.gate_atr:.6f}")

        for window_name in ['A', 'B', 'ALL', 'C']:
            res = results.get(window_name)
            if res is None:
                continue

            print(f"\n{'─'*70}")
            print(f"📊 Window {window_name}")
            print(f"{'─'*70}")

            print(f"\n💰 Performance:")
            print(f"   Trades: {res['n_trades']}")
            print(f"   Wins: {res['wins']} | Losses: {res['losses']}")
            print(f"   Win Rate: {res['winrate']:.1f}%")
            print(f"   PF: {res['pf']:.2f}")
            print(f"   Total R: {res['total_r']:+.2f}R")
            print(f"   Avg Win: {res['avg_win']:.2f}R")
            print(f"   Avg Loss: {res['avg_loss']:.2f}R")
            print(f"   Max DD: {res['max_dd']:.1f}%")

    def run_all_regimes(
        self,
        regimes: List[str] = ['LOW', 'NORMAL', 'HIGH'],
        n_particles: int = 30,
        max_iter: int = 50,
    ) -> Dict[str, Dict]:
        """Run PSO optimization for all regimes"""
        results = {}

        for regime in regimes:
            if regime not in self.regime_setups:
                print(f"⚠️  {regime} regime not found in data")
                continue

            result = self.optimize_regime(regime, n_particles, max_iter)
            if result:
                results[regime] = result
                self.print_results(result)

                # Save individual regime params
                params_file = Path(f'/home/noogh/projects/noogh_unified_system/src/data/params_{regime}.json')
                with open(params_file, 'w') as f:
                    json.dump(result['policy'].to_dict(), f, indent=2)
                print(f"\n💾 Saved: {params_file}")

        return results

    def print_final_summary(self, results: Dict[str, Dict]):
        """Print final comparison across all regimes"""
        print(f"\n{'='*70}")
        print(f"🎯 FINAL SUMMARY - ALL REGIMES")
        print(f"{'='*70}\n")

        # Table header
        print(f"{'Regime':<10} | {'Window':<6} | {'Trades':>6} | {'WR%':>6} | {'PF':>6} | {'Total R':>8} | {'DD%':>6}")
        print(f"{'-'*10}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*8}-+-{'-'*6}")

        for regime in ['LOW', 'NORMAL', 'HIGH']:
            if regime not in results:
                continue

            res_dict = results[regime]['results']

            for window_name in ['A', 'B', 'ALL', 'C']:
                res = res_dict.get(window_name)
                if res is None or res['n_trades'] == 0:
                    continue

                regime_str = regime if window_name == 'A' else ''
                print(f"{regime_str:<10} | {window_name:<6} | {res['n_trades']:6d} | "
                      f"{res['winrate']:6.1f} | {res['pf']:6.2f} | "
                      f"{res['total_r']:+8.2f} | {res['max_dd']:6.1f}")

            print(f"{'-'*10}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*8}-+-{'-'*6}")

        print(f"\n{'='*70}")
        print(f"✅ Multi-Regime Optimization Complete!")
        print(f"📁 Saved: params_LOW.json, params_NORMAL.json, params_HIGH.json")
        print(f"{'='*70}\n")


# ============================================================
# Main
# ============================================================

def main():
    """Run Multi-Regime PSO Optimization"""
    data_file = Path('/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl')

    # Initialize optimizer
    optimizer = MultiRegimeOptimizer(data_file)

    if len(optimizer.all_setups) < 50:
        print("❌ Not enough data")
        return

    # Run optimization for all regimes
    results = optimizer.run_all_regimes(
        regimes=['LOW', 'NORMAL', 'HIGH'],
        n_particles=30,
        max_iter=50,
    )

    # Print final summary
    optimizer.print_final_summary(results)

    # Save full results
    results_serializable = {}
    for regime, result in results.items():
        results_serializable[regime] = {
            'regime': regime,
            'fitness': result['fitness'],
            'policy': result['policy'].to_dict(),
            'results': result['results'],
            'history': result['history'],
            'data_stats': result['data_stats'],
        }

    results_file = Path('/home/noogh/projects/noogh_unified_system/src/data/multi_regime_pso_results.json')
    with open(results_file, 'w') as f:
        json.dump(results_serializable, f, indent=2)

    print(f"💾 Full results saved to: {results_file}\n")


if __name__ == "__main__":
    main()
