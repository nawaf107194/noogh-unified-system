#!/usr/bin/env python3
"""
Elite Neuron Evaluator - STRICT QUANT VERSION
================================
Evaluates Layer C (RunPod neurons) performance with:
- Layer B (Statistical Alpha Filter) ALWAYS ON ✅
- PAIR mode properly defined ✅
- PF calculated on R-multiples (not price %) ✅
- Window-based regime stability testing (A/B/ALL)
"""

import json
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load filters dynamically
import importlib.util
filter_path = Path(__file__).parent.parent / 'strategies' / 'brain_improved_filters.py'
spec = importlib.util.spec_from_file_location("brain_improved_filters", filter_path)
filters_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(filters_module)
improved_long_filter = filters_module.improved_long_filter
improved_short_filter = filters_module.improved_short_filter


# ============================================================
# Layer B: Statistical Alpha Filter (MUST ALWAYS BE ON)
# ============================================================

def statistical_alpha_filter(setup: Dict) -> Tuple[bool, str]:
    """
    Layer B filter - THIS MUST ALWAYS BE APPLIED

    Returns: (passed: bool, reason: str)
    """
    signal = setup.get('signal')

    if signal == 'LONG':
        return improved_long_filter(setup)
    elif signal == 'SHORT':
        return improved_short_filter(setup)
    else:
        return False, "Unknown signal type"


# ============================================================
# Elite Evaluator
# ============================================================

class EliteEvaluator:
    def __init__(self):
        self.data_file = Path('/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl')
        self.neurons_dir = Path('/home/noogh/projects/noogh_unified_system/src/neurons')

    def load_historical_data(self) -> List[Dict]:
        """Load all historical setups"""
        setups = []
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                for line in f:
                    setups.append(json.loads(line))

        # Sort by timestamp for window analysis
        setups.sort(key=lambda x: x.get('timestamp', ''))
        return setups

    def load_neuron(self, neuron_file: Path):
        """Load neuron from file"""
        try:
            spec = importlib.util.spec_from_file_location(neuron_file.stem, neuron_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find function (prefer long_filter or short_filter)
            if hasattr(module, 'long_filter'):
                return module.long_filter
            if hasattr(module, 'short_filter'):
                return module.short_filter

            # Fallback: find any callable function
            for attr_name in dir(module):
                if attr_name.startswith('_'):
                    continue
                attr = getattr(module, attr_name)
                if callable(attr) and not isinstance(attr, type):
                    return attr
            return None
        except Exception as e:
            print(f"❌ Error loading {neuron_file.name}: {e}")
            return None

    def calculate_r_multiple(self, setup: Dict) -> Optional[float]:
        """
        Calculate R-multiple for a trade
        R = (Exit - Entry) / Risk

        Risk = Entry - StopLoss (for LONG)
        Risk = StopLoss - Entry (for SHORT)
        """
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

    def evaluate_layer_c(
        self,
        setups: List[Dict],
        long_func,
        short_func,
        eval_mode: str = "PAIR",
        window_name: str = "ALL"
    ) -> Dict:
        """
        Evaluate Layer C neurons with STRICT rules:

        1. Layer B MUST be applied first ✅
        2. PAIR mode properly defined ✅
        3. PF calculated on R-multiples ✅

        eval_mode:
        - "LONG": Only evaluate LONG signals
        - "SHORT": Only evaluate SHORT signals
        - "PAIR": Evaluate both (LONG filter for LONG, SHORT filter for SHORT)
        """
        results = {
            'window': window_name,
            'mode': eval_mode,
            'total_setups': len(setups),
            'layer_b_passed': 0,
            'layer_c_passed': 0,
            'layer_c_rejected': 0,
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'win_r': 0.0,
            'loss_r': 0.0,
            'total_r': 0.0,
            'pf': 0.0,
            'winrate': 0.0,
            'avg_win_r': 0.0,
            'avg_loss_r': 0.0,
            'max_dd_r': 0.0,
            'equity_curve': [],
        }

        equity = 100.0  # Start with 100R
        peak = equity
        max_dd = 0.0

        win_r_sum = 0.0
        loss_r_sum = 0.0

        for setup in setups:
            signal = setup.get('signal')

            # ========================================
            # 🚨 FIX 1: Layer B MUST ALWAYS BE ON
            # ========================================
            ok_b, reason_b = statistical_alpha_filter(setup)
            if not ok_b:
                continue

            results['layer_b_passed'] += 1

            # ========================================
            # 🚨 FIX 2: PAIR mode properly defined
            # ========================================
            if eval_mode == "LONG" and signal != "LONG":
                continue

            if eval_mode == "SHORT" and signal != "SHORT":
                continue

            # PAIR mode: apply appropriate filter based on signal
            if signal == 'LONG':
                ok_c, conf_c, reason_c = long_func(setup)
            elif signal == 'SHORT':
                ok_c, conf_c, reason_c = short_func(setup)
            else:
                continue

            if not ok_c:
                results['layer_c_rejected'] += 1
                continue

            results['layer_c_passed'] += 1

            # ========================================
            # 🚨 FIX 3: PF calculated on R-multiples
            # ========================================
            r = self.calculate_r_multiple(setup)
            if r is None:
                continue

            results['trades'] += 1

            if r > 0:
                results['wins'] += 1
                win_r_sum += r
                results['win_r'] += r
            else:
                results['losses'] += 1
                loss_r_sum += abs(r)
                results['loss_r'] += abs(r)

            # Equity simulation (1R per trade risk)
            trade_pnl = r  # Direct R-multiple
            equity += trade_pnl

            # Track drawdown
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

            results['equity_curve'].append(equity)
            results['total_r'] += r

        # Calculate final metrics
        if results['trades'] > 0:
            results['winrate'] = (results['wins'] / results['trades']) * 100

        if results['wins'] > 0:
            results['avg_win_r'] = win_r_sum / results['wins']

        if results['losses'] > 0:
            results['avg_loss_r'] = loss_r_sum / results['losses']

        # Profit Factor (R-based)
        if results['loss_r'] > 0:
            results['pf'] = results['win_r'] / results['loss_r']
        else:
            results['pf'] = float('inf') if results['win_r'] > 0 else 0.0

        results['max_dd_r'] = max_dd * 100  # Convert to %
        results['final_equity'] = equity

        return results

    def evaluate_windows(
        self,
        long_func,
        short_func,
        eval_mode: str = "PAIR"
    ) -> Dict:
        """
        Evaluate across time windows for regime stability:
        - Window A: First half of data
        - Window B: Second half of data
        - Window ALL: All data
        """
        setups = self.load_historical_data()

        if not setups:
            print("❌ No data found")
            return {}

        # Split into windows
        mid = len(setups) // 2
        window_a = setups[:mid]
        window_b = setups[mid:]

        print(f"\n{'='*70}")
        print(f"🧪 ELITE EVALUATION - STRICT QUANT MODE")
        print(f"{'='*70}")
        print(f"Total setups: {len(setups)}")
        print(f"Window A: {len(window_a)} setups (first half)")
        print(f"Window B: {len(window_b)} setups (second half)")
        print(f"Eval mode: {eval_mode}")
        print(f"{'='*70}\n")

        results = {}

        # Evaluate each window
        for window_name, window_data in [
            ("A", window_a),
            ("B", window_b),
            ("ALL", setups)
        ]:
            print(f"\n{'─'*70}")
            print(f"📊 Window {window_name}")
            print(f"{'─'*70}")

            res = self.evaluate_layer_c(
                window_data,
                long_func,
                short_func,
                eval_mode,
                window_name
            )

            results[window_name] = res

            # Print results
            print(f"\n📈 Performance:")
            print(f"   Total setups: {res['total_setups']}")
            print(f"   Layer B passed: {res['layer_b_passed']} ({res['layer_b_passed']/res['total_setups']*100:.1f}%)")
            print(f"   Layer C passed: {res['layer_c_passed']}")
            print(f"   Layer C rejected: {res['layer_c_rejected']}")
            print(f"   Trades executed: {res['trades']}")

            print(f"\n💰 P&L:")
            print(f"   Wins: {res['wins']}")
            print(f"   Losses: {res['losses']}")
            print(f"   Win Rate: {res['winrate']:.1f}%")
            print(f"   Total R: {res['total_r']:+.2f}R")

            print(f"\n📊 Risk Metrics:")
            print(f"   Profit Factor: {res['pf']:.2f}")
            print(f"   Avg Win: {res['avg_win_r']:.2f}R")
            print(f"   Avg Loss: {res['avg_loss_r']:.2f}R")
            print(f"   Max DD: {res['max_dd_r']:.1f}%")
            print(f"   Final Equity: {res['final_equity']:.2f}R")

            # Stability verdict
            if window_name == "ALL":
                print(f"\n{'='*70}")
                self._print_stability_verdict(results)
                print(f"{'='*70}")

        return results

    def _print_stability_verdict(self, results: Dict):
        """Print regime stability verdict"""
        if 'A' not in results or 'B' not in results:
            return

        pf_a = results['A']['pf']
        pf_b = results['B']['pf']
        pf_all = results['ALL']['pf']

        dd_a = results['A']['max_dd_r']
        dd_b = results['B']['max_dd_r']
        dd_all = results['ALL']['max_dd_r']

        print(f"🎯 REGIME STABILITY VERDICT:")
        print(f"\n   PF Consistency:")
        print(f"      Window A: {pf_a:.2f}")
        print(f"      Window B: {pf_b:.2f}")
        print(f"      Window ALL: {pf_all:.2f}")

        # Check stability
        pf_stable = (pf_a > 1.5 and pf_b > 1.5)
        dd_safe = (dd_a < 20 and dd_b < 20 and dd_all < 25)

        print(f"\n   Verdict:")
        if pf_stable and dd_safe:
            print(f"      ✅ ELITE STABLE - Regime-independent alpha detected")
        elif pf_stable:
            print(f"      ⚠️  PROFITABLE but HIGH DD - Risk management needed")
        elif pf_all > 1.2:
            print(f"      ⚠️  REGIME-DEPENDENT - Works but not stable across time")
        else:
            print(f"      ❌ NO ALPHA - Below minimum threshold")


def main():
    """
    Main evaluation entry point
    """
    evaluator = EliteEvaluator()

    # Load latest elite neurons
    neuron_files = sorted(
        evaluator.neurons_dir.glob("*.py"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    if len(neuron_files) < 2:
        print("❌ Need at least 2 neurons (long_filter + short_filter)")
        return

    # Find long and short filters
    long_filter = None
    short_filter = None

    for nf in neuron_files:
        if 'long' in nf.name.lower() and long_filter is None:
            long_filter = evaluator.load_neuron(nf)
            print(f"✅ Loaded LONG filter: {nf.name}")

        if 'short' in nf.name.lower() and short_filter is None:
            short_filter = evaluator.load_neuron(nf)
            print(f"✅ Loaded SHORT filter: {nf.name}")

        if long_filter and short_filter:
            break

    if not long_filter or not short_filter:
        print("❌ Could not find both LONG and SHORT filters")
        return

    # Run evaluation in PAIR mode
    results = evaluator.evaluate_windows(
        long_filter,
        short_filter,
        eval_mode="PAIR"
    )

    # Save results
    results_file = Path('/home/noogh/projects/noogh_unified_system/src/data/elite_evaluation.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: {results_file}")


if __name__ == "__main__":
    main()
