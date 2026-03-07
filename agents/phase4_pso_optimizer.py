#!/usr/bin/env python3
"""
Phase 4: Parametric Evolution Engine (PSO)
==========================================
Optimizes FIXED structure with VARIABLE parameters over Layer B filtered data

Architecture:
- Layer B: Statistical Alpha Gate (always on)
- Layer C: Linear Score Policy with learnable weights

Goal: Find optimal (w1..w8, threshold) that maximize fitness
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


# ============================================================
# Evaluator (Layer B → Layer C → Metrics)
# ============================================================

class PolicyEvaluator:
    def __init__(self, data_file: Path):
        self.data_file = data_file
        self.setups = []
        self.load_data()

    def load_data(self):
        """Load and filter through Layer B"""
        if not self.data_file.exists():
            return

        with open(self.data_file, 'r') as f:
            for line in f:
                setup = json.loads(line)

                # Layer B filter
                ok_b, _ = statistical_alpha_filter(setup)
                if not ok_b:
                    continue

                self.setups.append(setup)

        # Sort by timestamp
        self.setups.sort(key=lambda x: x.get('timestamp', ''))

        print(f"✅ Loaded {len(self.setups)} setups (after Layer B filtering)")

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
        window: str = "ALL"
    ) -> Dict:
        """
        Evaluate policy on setups

        Returns metrics: {pf, dd, winrate, n_trades, total_r, ...}
        """
        # Select window
        if window == "A":
            data = self.setups[:len(self.setups)//2]
        elif window == "B":
            data = self.setups[len(self.setups)//2:]
        else:
            data = self.setups

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
            'window': window,
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
        mode: str = "robust"
    ) -> float:
        """
        Calculate fitness score

        Modes:
        - "robust": 0.7*train + 0.3*val with stability penalty
        - "aggressive": train only
        """
        res_a = self.evaluate(policy, "A")
        res_b = self.evaluate(policy, "B")
        res_all = self.evaluate(policy, "ALL")

        # Kill conditions
        if res_all['n_trades'] < 10:
            return 0.0
        if res_all['pf'] <= 1.0:
            return 0.0
        if res_all['max_dd'] > 30:
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
            n_bonus = min(res['n_trades'] / 50, 1.0)

            return (pf_norm * 0.4 + exp_norm * 0.3 + dd_penalty * 0.2 + n_bonus * 0.1)

        score_a = score_single(res_a)
        score_b = score_single(res_b)

        if mode == "robust":
            # Weighted + stability
            base = 0.7 * score_a + 0.3 * score_b
            stability = min(score_a, score_b) / max(score_a, score_b, 1e-9)
            return base * stability
        else:
            return score_a


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
        n_particles: int = 30,
        max_iter: int = 50,
        w: float = 0.7,
        c1: float = 1.5,
        c2: float = 1.5,
    ):
        self.evaluator = evaluator
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
        print(f"\n{'='*70}")
        print(f"🧬 PSO Optimization Started")
        print(f"{'='*70}")
        print(f"Particles: {self.n_particles}")
        print(f"Max Iterations: {self.max_iter}")
        print(f"Search Space: {self.dim}D")
        print(f"{'='*70}\n")

        # Initial evaluation
        for i in range(self.n_particles):
            policy = self.params_to_policy(self.positions[i])
            fit = self.evaluator.fitness(policy)
            self.pbest_fit[i] = fit

            if fit > self.gbest_fit:
                self.gbest_fit = fit
                self.gbest_pos = self.positions[i].copy()

        print(f"📊 Initial Best Fitness: {self.gbest_fit:.4f}")

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
                fit = self.evaluator.fitness(policy)

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
                print(f"Iter {iter_num+1:3d}/{self.max_iter} | "
                      f"Best: {self.gbest_fit:.4f} | "
                      f"Avg: {avg_fit:.4f}")

            self.history.append({
                'iter': iter_num + 1,
                'gbest': self.gbest_fit,
                'avg': float(np.mean(self.pbest_fit)),
            })

        print(f"\n{'='*70}")
        print(f"✅ Optimization Complete!")
        print(f"🏆 Best Fitness: {self.gbest_fit:.4f}")
        print(f"{'='*70}\n")

        best_policy = self.params_to_policy(self.gbest_pos)
        return best_policy, self.gbest_fit


# ============================================================
# Main
# ============================================================

def main():
    """Run Phase 4 optimization"""
    data_file = Path('/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl')

    # Initialize evaluator
    evaluator = PolicyEvaluator(data_file)

    if len(evaluator.setups) < 20:
        print("❌ Not enough data after Layer B filtering")
        return

    # Run PSO
    pso = PSO(
        evaluator,
        n_particles=30,
        max_iter=50,
    )

    best_policy, best_fitness = pso.optimize()

    # Evaluate best policy on all windows
    print(f"\n{'='*70}")
    print(f"📊 BEST POLICY EVALUATION")
    print(f"{'='*70}")

    print(f"\n🔧 Parameters:")
    print(f"   Weights: {best_policy.weights}")
    print(f"   Threshold: {best_policy.threshold:.4f}")
    print(f"   Gate ATR: {best_policy.gate_atr:.6f}")

    for window in ["A", "B", "ALL"]:
        print(f"\n{'─'*70}")
        print(f"📊 Window {window}")
        print(f"{'─'*70}")

        res = evaluator.evaluate(best_policy, window)

        print(f"\n💰 Performance:")
        print(f"   Trades: {res['n_trades']}")
        print(f"   Wins: {res['wins']} | Losses: {res['losses']}")
        print(f"   Win Rate: {res['winrate']:.1f}%")
        print(f"   PF: {res['pf']:.2f}")
        print(f"   Total R: {res['total_r']:+.2f}R")
        print(f"   Avg Win: {res['avg_win']:.2f}R")
        print(f"   Avg Loss: {res['avg_loss']:.2f}R")
        print(f"   Max DD: {res['max_dd']:.1f}%")

    # Save results
    results = {
        'fitness': best_fitness,
        'policy': {
            'weights': best_policy.weights.tolist(),
            'threshold': float(best_policy.threshold),
            'gate_atr': float(best_policy.gate_atr),
        },
        'features': FEATURES,
        'windows': {
            'A': evaluator.evaluate(best_policy, "A"),
            'B': evaluator.evaluate(best_policy, "B"),
            'ALL': evaluator.evaluate(best_policy, "ALL"),
        },
        'history': pso.history,
    }

    results_file = Path('/home/noogh/projects/noogh_unified_system/src/data/phase4_pso_results.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"💾 Results saved to: {results_file}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
