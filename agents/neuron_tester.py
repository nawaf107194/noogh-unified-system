#!/usr/bin/env python3
"""
Neuron Tester - اختبار العصبونات المُولَّدة على البيانات التاريخية
"""
import json
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

class NeuronTester:
    def __init__(self):
        self.data_file = Path('/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl')
        self.neurons_dir = Path('/home/noogh/projects/noogh_unified_system/src/neurons')
        self.results_file = Path('/home/noogh/projects/noogh_unified_system/src/data/neuron_test_results.json')

    def load_historical_data(self) -> List[Dict]:
        """تحميل البيانات التاريخية"""
        setups = []
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                for line in f:
                    setups.append(json.loads(line))
        return setups

    def load_neuron(self, neuron_file: Path):
        """تحميل عصبون من ملف Python"""
        try:
            spec = importlib.util.spec_from_file_location(neuron_file.stem, neuron_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # البحث عن أول function في الملف
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if callable(attr) and not attr_name.startswith('_'):
                    return attr
            return None
        except Exception as e:
            print(f"❌ Error loading {neuron_file.name}: {e}")
            return None

    def test_neuron(self, neuron_func, setups: List[Dict]) -> Dict:
        """اختبار عصبون على البيانات"""
        results = {
            'total_tested': 0,
            'passed': 0,
            'rejected': 0,
            'errors': 0,
            'wins_passed': 0,
            'losses_passed': 0,
            'wins_rejected': 0,
            'losses_rejected': 0,
            'confidence_avg': 0.0
        }

        confidences = []

        for setup in setups:
            results['total_tested'] += 1

            try:
                passed, confidence, reason = neuron_func(setup)

                if passed:
                    results['passed'] += 1
                    confidences.append(confidence)
                    if setup.get('outcome') == 'WIN':
                        results['wins_passed'] += 1
                    else:
                        results['losses_passed'] += 1
                else:
                    results['rejected'] += 1
                    if setup.get('outcome') == 'WIN':
                        results['wins_rejected'] += 1
                    else:
                        results['losses_rejected'] += 1

            except Exception as e:
                results['errors'] += 1

        if confidences:
            results['confidence_avg'] = sum(confidences) / len(confidences)

        # حساب Win Rate للإشارات التي نجحت
        if results['passed'] > 0:
            results['winrate_passed'] = results['wins_passed'] / results['passed'] * 100
        else:
            results['winrate_passed'] = 0

        # حساب Win Rate للإشارات المرفوضة
        if results['rejected'] > 0:
            results['winrate_rejected'] = results['wins_rejected'] / results['rejected'] * 100
        else:
            results['winrate_rejected'] = 0

        # حساب Improvement
        baseline_wr = (results['wins_passed'] + results['wins_rejected']) / results['total_tested'] * 100
        results['improvement'] = results['winrate_passed'] - baseline_wr

        return results

    def test_all_neurons(self) -> Dict:
        """اختبار كل العصبونات"""
        print("\n" + "="*70)
        print("🧪 NEURON TESTING - Testing all generated neurons")
        print("="*70)

        setups = self.load_historical_data()
        print(f"\n📥 Loaded {len(setups)} historical setups")

        neuron_files = sorted(self.neurons_dir.glob("*.py"), key=lambda x: x.stat().st_mtime, reverse=True)

        all_results = {}

        for neuron_file in neuron_files:
            print(f"\n{'─'*70}")
            print(f"🧠 Testing: {neuron_file.name}")
            print(f"{'─'*70}")

            neuron_func = self.load_neuron(neuron_file)
            if not neuron_func:
                continue

            results = self.test_neuron(neuron_func, setups)
            all_results[neuron_file.stem] = results

            print(f"\n📊 Results:")
            print(f"   Total Tested: {results['total_tested']}")
            print(f"   Passed: {results['passed']} ({results['passed']/results['total_tested']*100:.1f}%)")
            print(f"   Rejected: {results['rejected']} ({results['rejected']/results['total_tested']*100:.1f}%)")
            print(f"   Errors: {results['errors']}")

            print(f"\n✅ Passed Signals:")
            print(f"   Wins: {results['wins_passed']}")
            print(f"   Losses: {results['losses_passed']}")
            print(f"   WinRate: {results['winrate_passed']:.1f}%")
            print(f"   Avg Confidence: {results['confidence_avg']:.2f}")

            print(f"\n🚫 Rejected Signals:")
            print(f"   Wins: {results['wins_rejected']}")
            print(f"   Losses: {results['losses_rejected']}")
            print(f"   WinRate: {results['winrate_rejected']:.1f}%")

            improvement_color = "🟢" if results['improvement'] > 0 else "🔴"
            print(f"\n{improvement_color} Improvement: {results['improvement']:+.1f}%")

        # حفظ النتائج
        with open(self.results_file, 'w') as f:
            json.dump(all_results, f, indent=2)

        print(f"\n{'='*70}")
        print(f"💾 Results saved to: {self.results_file}")
        print(f"{'='*70}\n")

        return all_results

    def find_best_neurons(self, results: Dict) -> List[Tuple[str, float]]:
        """إيجاد أفضل العصبونات"""
        ranked = []
        for name, res in results.items():
            if res['passed'] > 0:  # يجب أن يكون لديه إشارات ناجحة
                score = res['improvement']
                ranked.append((name, score))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked


def main():
    tester = NeuronTester()
    results = tester.test_all_neurons()

    best_neurons = tester.find_best_neurons(results)

    if best_neurons:
        print("\n" + "="*70)
        print("🏆 BEST NEURONS (by improvement)")
        print("="*70)
        for i, (name, score) in enumerate(best_neurons[:5], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            print(f"{emoji} {i}. {name}: {score:+.1f}%")
        print("="*70 + "\n")


if __name__ == "__main__":
    main()
