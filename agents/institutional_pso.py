#!/usr/bin/env python3
"""
Phase 4.2: Institutional-Grade PSO Optimization
================================================
Production-ready optimization with:
- Regularized PSO (bounded weights, L2 penalty)
- Walk-forward validation (60/20/20)
- Monte Carlo permutation tests
- Bootstrapped confidence intervals
- Statistical rigor checks
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import sys
from scipy import stats

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
# Feature Extraction
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
# Policy (Regularized)
# ============================================================

@dataclass
class Policy:
    """Linear score policy with gate (regularized)"""
    weights: np.ndarray  # shape (7,)
    threshold: float
    gate_atr: float

    def __call__(self, features: np.ndarray) -> Tuple[bool, float]:
        """Evaluate policy on features"""
        if features[0] > self.gate_atr:
            return False, 0.0

        score = np.dot(self.weights, features)
        passed = score > self.threshold

        return passed, score

    def to_dict(self) -> Dict:
        """Convert to JSON"""
        return {
            'weights': self.weights.tolist(),
            'threshold': float(self.threshold),
            'gate_atr': float(self.gate_atr),
            'features': FEATURES,
        }


# ============================================================
# Evaluator
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

        if signal == 'LONG':
            risk = entry - sl
            if outcome == 'WIN':
                pnl = tp - entry
            else:
                pnl = sl - entry
        else:  # SHORT
            risk = sl - entry
            if outcome == 'WIN':
                pnl = entry - tp
            else:
                pnl = entry - sl

        if risk <= 0:
            return None

        return pnl / risk

    def evaluate(
        self,
        policy: Policy,
        data: List[Dict],
        window_name: str = "ALL"
    ) -> Dict:
        """Evaluate policy on setups"""
        trades = 0
        wins = 0
        losses = 0
        win_r = 0.0
        loss_r = 0.0
        total_r = 0.0

        r_multiples = []  # For detailed statistics

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
            r_multiples.append(r)

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
        if loss_r > 0:
            pf = win_r / loss_r
        elif win_r > 0:
            pf = float('inf')  # All wins, no losses
        else:
            pf = 0  # No trades
        avg_win = (win_r / wins) if wins > 0 else 0
        avg_loss = (loss_r / losses) if losses > 0 else 0

        # Expectancy
        expectancy = total_r / trades if trades > 0 else 0

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
            'expectancy': expectancy,
            'r_multiples': r_multiples,  # For statistical tests
        }

    def fitness(
        self,
        policy: Policy,
        train_data: List[Dict],
        val_data: List[Dict],
        regularization: float = 0.05
    ) -> float:
        """
        Calculate fitness with L2 regularization

        Args:
            policy: Policy to evaluate
            train_data: Training setups
            val_data: Validation setups
            regularization: L2 penalty coefficient

        Returns:
            Fitness score (higher is better)
        """
        res_train = self.evaluate(policy, train_data, "TRAIN")
        res_val = self.evaluate(policy, val_data, "VAL")

        # Kill conditions
        if res_train['n_trades'] < 10:
            return 0.0
        if res_train['pf'] <= 1.0:
            return 0.0
        if res_train['max_dd'] > 30:
            return 0.0

        # Fitness components
        def score_single(res):
            pf_norm = min(res['pf'], 3.0) / 3.0
            exp_norm = np.tanh(res['expectancy'] * 2)
            dd_penalty = np.exp(-res['max_dd'] / 10)
            n_bonus = min(res['n_trades'] / 50, 1.0)
            return (pf_norm * 0.4 + exp_norm * 0.3 + dd_penalty * 0.2 + n_bonus * 0.1)

        score_train = score_single(res_train)
        score_val = score_single(res_val) if res_val['n_trades'] > 0 else 0

        # Weighted + stability
        base = 0.7 * score_train + 0.3 * score_val
        stability = min(score_train, score_val) / max(score_train, score_val, 1e-9)

        # L2 Regularization (penalize large weights)
        l2_penalty = regularization * np.sum(policy.weights**2)

        return base * stability - l2_penalty


# ============================================================
# Regularized PSO
# ============================================================

class RegularizedPSO:
    """PSO with tighter bounds and L2 regularization"""

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
        regularization: float = 0.05,
    ):
        self.evaluator = evaluator
        self.train_data = train_data
        self.val_data = val_data
        self.n_particles = n_particles
        self.max_iter = max_iter
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.regularization = regularization

        # REGULARIZED BOUNDS (tighter than [-2, 2])
        self.dim = N_FEATURES + 2
        self.lb = np.array([-1.0] * N_FEATURES + [-3.0, 0.0])
        self.ub = np.array([1.0] * N_FEATURES + [3.0, 0.015])

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
        print(f"🧬 REGULARIZED PSO OPTIMIZATION")
        print(f"{'='*70}")
        print(f"Particles: {self.n_particles}")
        print(f"Max Iterations: {self.max_iter}")
        print(f"Weight Bounds: [-1.0, 1.0] (regularized)")
        print(f"L2 Regularization: {self.regularization}")
        print(f"{'='*70}\n")

        # Initial evaluation
        for i in range(self.n_particles):
            policy = self.params_to_policy(self.positions[i])
            fit = self.evaluator.fitness(
                policy, self.train_data, self.val_data, self.regularization
            )
            self.pbest_fit[i] = fit

            if fit > self.gbest_fit:
                self.gbest_fit = fit
                self.gbest_pos = self.positions[i].copy()

        print(f"📊 Initial Best Fitness: {self.gbest_fit:.4f}")

        # Main loop
        for iter_num in range(self.max_iter):
            for i in range(self.n_particles):
                r1 = np.random.random(self.dim)
                r2 = np.random.random(self.dim)

                self.velocities[i] = (
                    self.w * self.velocities[i]
                    + self.c1 * r1 * (self.pbest_pos[i] - self.positions[i])
                    + self.c2 * r2 * (self.gbest_pos - self.positions[i])
                )

                self.positions[i] += self.velocities[i]
                self.positions[i] = np.clip(self.positions[i], self.lb, self.ub)

                policy = self.params_to_policy(self.positions[i])
                fit = self.evaluator.fitness(
                    policy, self.train_data, self.val_data, self.regularization
                )

                if fit > self.pbest_fit[i]:
                    self.pbest_fit[i] = fit
                    self.pbest_pos[i] = self.positions[i].copy()

                if fit > self.gbest_fit:
                    self.gbest_fit = fit
                    self.gbest_pos = self.positions[i].copy()

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
# Statistical Validation
# ============================================================

class StatisticalValidator:
    """Monte Carlo and Bootstrap validation"""

    def __init__(self, evaluator: PolicyEvaluator):
        self.evaluator = evaluator

    def monte_carlo_permutation_test(
        self,
        policy: Policy,
        data: List[Dict],
        n_permutations: int = 500,
        metric: str = 'pf'
    ) -> Dict:
        """
        Monte Carlo permutation test

        Randomly permute trade outcomes to test if PF is significant

        Returns:
            {
                'observed_metric': float,
                'permuted_distribution': [floats],
                'p_value': float,
                'is_significant': bool
            }
        """
        print(f"\n{'='*70}")
        print(f"🎲 MONTE CARLO PERMUTATION TEST")
        print(f"{'='*70}")
        print(f"Permutations: {n_permutations}")
        print(f"Metric: {metric.upper()}")
        print(f"{'='*70}\n")

        # Get observed metric
        res_observed = self.evaluator.evaluate(policy, data, "OBSERVED")
        observed_value = res_observed[metric]

        # Handle inf values (cap at 100 for comparison purposes)
        if np.isinf(observed_value):
            observed_value = 100.0

        print(f"📊 Observed {metric.upper()}: {observed_value:.4f}")

        # Permutation test
        permuted_values = []

        for i in range(n_permutations):
            # Shuffle outcomes while keeping features intact
            shuffled_data = data.copy()
            outcomes = [s['outcome'] for s in shuffled_data]
            np.random.shuffle(outcomes)

            for j, outcome in enumerate(outcomes):
                shuffled_data[j] = shuffled_data[j].copy()
                shuffled_data[j]['outcome'] = outcome

            res_perm = self.evaluator.evaluate(policy, shuffled_data, "PERMUTED")
            perm_val = res_perm[metric]

            # Handle inf values (cap at 100)
            if np.isinf(perm_val):
                perm_val = 100.0

            permuted_values.append(perm_val)

            if (i + 1) % 100 == 0:
                print(f"   Progress: {i+1}/{n_permutations}")

        permuted_values = np.array(permuted_values)

        # Calculate p-value (two-tailed)
        p_value = np.mean(np.abs(permuted_values) >= np.abs(observed_value))

        is_significant = p_value < 0.05

        print(f"\n📈 Results:")
        print(f"   Observed: {observed_value:.4f}")
        print(f"   Permuted Mean: {permuted_values.mean():.4f}")
        print(f"   Permuted Std: {permuted_values.std():.4f}")
        print(f"   P-value: {p_value:.4f}")
        print(f"   Significant (p < 0.05): {'✅ YES' if is_significant else '❌ NO'}")

        return {
            'observed_metric': observed_value,
            'permuted_distribution': permuted_values.tolist(),
            'permuted_mean': float(permuted_values.mean()),
            'permuted_std': float(permuted_values.std()),
            'p_value': float(p_value),
            'is_significant': is_significant,
        }

    def bootstrap_confidence_interval(
        self,
        policy: Policy,
        data: List[Dict],
        n_bootstrap: int = 1000,
        metric: str = 'pf',
        confidence: float = 0.95
    ) -> Dict:
        """
        Bootstrap confidence intervals

        Resample trades with replacement to estimate CI

        Returns:
            {
                'mean': float,
                'ci_lower': float,
                'ci_upper': float,
                'distribution': [floats]
            }
        """
        print(f"\n{'='*70}")
        print(f"🔁 BOOTSTRAP CONFIDENCE INTERVAL")
        print(f"{'='*70}")
        print(f"Bootstrap Samples: {n_bootstrap}")
        print(f"Metric: {metric.upper()}")
        print(f"Confidence Level: {confidence*100:.0f}%")
        print(f"{'='*70}\n")

        bootstrap_values = []

        for i in range(n_bootstrap):
            # Resample with replacement
            resampled_data = np.random.choice(data, size=len(data), replace=True).tolist()

            res_boot = self.evaluator.evaluate(policy, resampled_data, "BOOTSTRAP")
            boot_val = res_boot[metric]

            # Handle inf values (cap at 100)
            if np.isinf(boot_val):
                boot_val = 100.0

            bootstrap_values.append(boot_val)

            if (i + 1) % 200 == 0:
                print(f"   Progress: {i+1}/{n_bootstrap}")

        bootstrap_values = np.array(bootstrap_values)

        # Calculate CI
        alpha = 1 - confidence
        ci_lower = np.percentile(bootstrap_values, alpha/2 * 100)
        ci_upper = np.percentile(bootstrap_values, (1 - alpha/2) * 100)

        print(f"\n📊 Results:")
        print(f"   Mean: {bootstrap_values.mean():.4f}")
        print(f"   {confidence*100:.0f}% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
        print(f"   Robust: {'✅ YES' if ci_lower > 1.1 else '❌ NO (lower bound ≤ 1.1)'}")

        return {
            'mean': float(bootstrap_values.mean()),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'distribution': bootstrap_values.tolist(),
        }


# ============================================================
# Main Pipeline
# ============================================================

def load_data(filename: str = "backtest_setups_12M.jsonl") -> List[Dict]:
    """Load setups from JSONL"""
    data_file = Path('/home/noogh/projects/noogh_unified_system/src/data') / filename

    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return []

    setups = []
    with open(data_file, 'r') as f:
        for line in f:
            setups.append(json.loads(line))

    # Sort by timestamp (temporal ordering)
    setups.sort(key=lambda x: x.get('timestamp', ''))

    print(f"✅ Loaded {len(setups)} setups from {filename}")
    print(f"   Date range: {setups[0]['timestamp']} → {setups[-1]['timestamp']}")

    return setups


def main():
    """Run institutional-grade PSO pipeline"""
    print("="*70)
    print("🏛️ INSTITUTIONAL-GRADE PSO OPTIMIZATION")
    print("="*70)

    # Load data
    setups = load_data("backtest_setups_12M.jsonl")

    if len(setups) < 100:
        print("❌ Not enough data")
        return

    # Walk-forward split (60/20/20)
    split1 = int(len(setups) * 0.6)
    split2 = int(len(setups) * 0.8)

    train = setups[:split1]
    val = setups[split1:split2]
    oos = setups[split2:]

    print(f"\n📊 Walk-Forward Split (60/20/20):")
    print(f"   Train: {len(train)} setups (60%)")
    print(f"   Val: {len(val)} setups (20%)")
    print(f"   OOS: {len(oos)} setups (20%)")

    # Initialize evaluator
    evaluator = PolicyEvaluator(setups)

    # Run regularized PSO
    pso = RegularizedPSO(
        evaluator,
        train,
        val,
        n_particles=30,
        max_iter=50,
        regularization=0.05
    )

    best_policy, best_fitness = pso.optimize()

    # Evaluate on all windows
    print(f"\n{'='*70}")
    print(f"📊 POLICY EVALUATION")
    print(f"{'='*70}")

    print(f"\n🔧 Learned Parameters:")
    print(f"   Weights: {best_policy.weights}")
    print(f"   Threshold: {best_policy.threshold:.4f}")
    print(f"   Gate ATR: {best_policy.gate_atr:.6f}")

    # Check for boundary saturation
    saturated = np.sum((np.abs(best_policy.weights) > 0.95))
    if saturated > 0:
        print(f"\n⚠️  WARNING: {saturated}/{N_FEATURES} weights near bounds (>0.95)")
        print(f"   This may indicate overfitting!")

    results = {}

    for window_name, window_data in [
        ("TRAIN", train),
        ("VAL", val),
        ("OOS", oos),
        ("ALL", setups)
    ]:
        print(f"\n{'─'*70}")
        print(f"📊 Window {window_name}")
        print(f"{'─'*70}")

        res = evaluator.evaluate(best_policy, window_data, window_name)
        results[window_name] = res

        print(f"\n💰 Performance:")
        print(f"   Trades: {res['n_trades']}")
        print(f"   Wins: {res['wins']} | Losses: {res['losses']}")
        print(f"   Win Rate: {res['winrate']:.1f}%")
        print(f"   PF: {res['pf']:.2f}")
        print(f"   Total R: {res['total_r']:+.2f}R")
        print(f"   Expectancy: {res['expectancy']:+.3f}R")
        print(f"   Max DD: {res['max_dd']:.1f}%")

    # Statistical validation on OOS
    validator = StatisticalValidator(evaluator)

    # Monte Carlo test
    mc_result = validator.monte_carlo_permutation_test(
        best_policy,
        oos,
        n_permutations=500,
        metric='pf'
    )

    # Bootstrap CI
    boot_result = validator.bootstrap_confidence_interval(
        best_policy,
        oos,
        n_bootstrap=1000,
        metric='pf',
        confidence=0.95
    )

    # Save results (convert numpy bools to Python bools)
    def convert_types(obj):
        """Recursively convert numpy types to Python types"""
        if isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(v) for v in obj]
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, float) and (np.isinf(obj) or np.isnan(obj)):
            return None  # JSON doesn't support inf/nan
        else:
            return obj

    final_results = {
        'policy': best_policy.to_dict(),
        'fitness': best_fitness,
        'windows': convert_types(results),
        'monte_carlo': convert_types(mc_result),
        'bootstrap': convert_types(boot_result),
        'history': pso.history,
        'data_stats': {
            'total': len(setups),
            'train': len(train),
            'val': len(val),
            'oos': len(oos),
        }
    }

    results_file = Path('/home/noogh/projects/noogh_unified_system/src/data/institutional_pso_results.json')
    with open(results_file, 'w') as f:
        json.dump(final_results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"💾 Results saved to: {results_file}")
    print(f"{'='*70}\n")

    # Final verdict
    print(f"{'='*70}")
    print(f"🎯 FINAL VERDICT")
    print(f"{'='*70}")

    oos_res = results['OOS']

    print(f"\n📊 OOS Performance:")
    print(f"   PF: {oos_res['pf']:.2f}")
    print(f"   Expectancy: {oos_res['expectancy']:+.3f}R")
    print(f"   Max DD: {oos_res['max_dd']:.1f}%")
    print(f"   Trades: {oos_res['n_trades']}")

    print(f"\n🎲 Statistical Significance:")
    print(f"   Monte Carlo p-value: {mc_result['p_value']:.4f}")
    print(f"   Significant: {'✅ YES' if mc_result['is_significant'] else '❌ NO'}")

    print(f"\n🔁 Robustness (Bootstrap 95% CI):")
    print(f"   PF CI: [{boot_result['ci_lower']:.2f}, {boot_result['ci_upper']:.2f}]")
    print(f"   Robust: {'✅ YES' if boot_result['ci_lower'] > 1.1 else '❌ NO'}")

    # Overall verdict
    is_production_ready = (
        oos_res['pf'] > 1.3
        and oos_res['max_dd'] < 20
        and oos_res['n_trades'] >= 20
        and mc_result['is_significant']
        and boot_result['ci_lower'] > 1.1
    )

    print(f"\n{'='*70}")
    if is_production_ready:
        print(f"✅ PRODUCTION READY - Alpha survives institutional rigor")
    else:
        print(f"❌ NOT PRODUCTION READY - Alpha too fragile")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    # Set random seed for reproducibility
    np.random.seed(42)
    main()
