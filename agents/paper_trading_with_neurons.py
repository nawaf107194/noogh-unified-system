#!/usr/bin/env python3
"""
Paper Trading Agent with RunPod Neurons
يستخدم العصبونات المُولَّدة لتداول وهمي وجمع النتائج
"""
import asyncio
import json
import sys
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading.binance_futures import BinanceFutures
from trading.trap_hybrid_engine import TrapHybridEngine

class PaperTradingWithNeurons:
    def __init__(self):
        self.binance = BinanceFutures()
        self.trap_engine = TrapHybridEngine(self.binance)
        self.neurons_dir = Path('/home/noogh/projects/noogh_unified_system/src/neurons')
        self.results_file = Path('/home/noogh/projects/noogh_unified_system/src/data/paper_trades_with_neurons.jsonl')

        # قائمة العملات للمراقبة
        self.symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT',
            'DOGEUSDT', 'XRPUSDT', 'DOTUSDT', 'MATICUSDT', 'AVAXUSDT'
        ]

        self.neurons = []
        self.load_best_neurons()

    def load_best_neurons(self):
        """تحميل أفضل العصبونات"""
        # تحميل نتائج الاختبار
        results_file = Path('/home/noogh/projects/noogh_unified_system/src/data/neuron_test_results.json')

        if results_file.exists():
            with open(results_file, 'r') as f:
                test_results = json.load(f)

            # ترتيب العصبونات حسب الأداء
            ranked = [(name, res['improvement']) for name, res in test_results.items()
                     if res.get('passed', 0) > 0]
            ranked.sort(key=lambda x: x[1], reverse=True)

            # تحميل أفضل 3 عصبونات
            for name, score in ranked[:3]:
                neuron_file = self.neurons_dir / f"{name}.py"
                if neuron_file.exists():
                    neuron_func = self.load_neuron(neuron_file)
                    if neuron_func:
                        self.neurons.append({
                            'name': name,
                            'function': neuron_func,
                            'score': score
                        })
                        print(f"✅ Loaded neuron: {name} (improvement: {score:+.1f}%)")

        if not self.neurons:
            print("⚠️  No neurons loaded. Will use Trap strategy only.")

    def load_neuron(self, neuron_file: Path):
        """تحميل عصبون من ملف"""
        try:
            spec = importlib.util.spec_from_file_location(neuron_file.stem, neuron_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if callable(attr) and not attr_name.startswith('_'):
                    return attr
            return None
        except Exception as e:
            print(f"❌ Error loading {neuron_file.name}: {e}")
            return None

    def apply_neurons(self, setup: Dict) -> Dict:
        """تطبيق العصبونات على setup"""
        results = {
            'passed': True,
            'rejected_by': [],
            'confidences': [],
            'reasons': []
        }

        for neuron in self.neurons:
            try:
                passed, confidence, reason = neuron['function'](setup)

                if not passed:
                    results['passed'] = False
                    results['rejected_by'].append(neuron['name'])
                    results['reasons'].append(reason)
                else:
                    results['confidences'].append(confidence)
                    results['reasons'].append(reason)
            except Exception as e:
                print(f"❌ Neuron {neuron['name']} error: {e}")

        # حساب متوسط الثقة
        if results['confidences']:
            results['avg_confidence'] = sum(results['confidences']) / len(results['confidences'])
        else:
            results['avg_confidence'] = 0.0

        return results

    async def scan_markets(self):
        """مسح الأسواق للإشارات"""
        signals = []

        for symbol in self.symbols:
            df = self.binance.get_klines(symbol, '15m', limit=100)
            if df is None or df.empty:
                continue

            trap_signal = self.trap_engine.detect_trap(df, symbol)
            if trap_signal:
                # تحضير setup data
                setup = {
                    'symbol': symbol,
                    'signal': trap_signal.signal,
                    'entry_price': trap_signal.entry_price,
                    'stop_loss': trap_signal.stop_loss,
                    'quick_tp': trap_signal.quick_tp,
                    'atr': trap_signal.atr,
                    'reasons': trap_signal.reasons,
                    'taker_buy_ratio': 0.55,  # TODO: حساب من البيانات الحقيقية
                    'volume': df['volume'].iloc[-1],
                    'timestamp': datetime.now().isoformat()
                }

                # تطبيق العصبونات
                neuron_results = self.apply_neurons(setup)
                setup['neuron_results'] = neuron_results

                if neuron_results['passed']:
                    signals.append(setup)
                    print(f"\n✅ Signal PASSED: {symbol} {trap_signal.signal}")
                    print(f"   Confidence: {neuron_results['avg_confidence']:.2f}")
                    print(f"   Reasons: {', '.join(neuron_results['reasons'][:2])}")
                else:
                    print(f"\n🚫 Signal REJECTED: {symbol} {trap_signal.signal}")
                    print(f"   Rejected by: {', '.join(neuron_results['rejected_by'])}")
                    print(f"   Reasons: {', '.join(neuron_results['reasons'][:2])}")

        return signals

    def save_paper_trade(self, setup: Dict):
        """حفظ صفقة وهمية"""
        with open(self.results_file, 'a') as f:
            f.write(json.dumps(setup) + '\n')

    async def run_cycle(self):
        """دورة واحدة من Paper Trading"""
        print(f"\n{'='*70}")
        print(f"🎯 Paper Trading Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        print(f"📊 Monitoring {len(self.symbols)} symbols...")
        print(f"🧠 Using {len(self.neurons)} neurons")

        signals = await self.scan_markets()

        print(f"\n📈 Found {len(signals)} signals that passed neuron filters")

        for signal in signals:
            self.save_paper_trade(signal)

        print(f"\n{'='*70}\n")

    async def run_continuous(self, cycles: int = 10, interval: int = 300):
        """تشغيل مستمر"""
        print(f"\n🚀 Starting Paper Trading with Neurons")
        print(f"   Cycles: {cycles}")
        print(f"   Interval: {interval}s ({interval/60:.0f} min)")
        print(f"   Results: {self.results_file}")

        for i in range(cycles):
            print(f"\n\n{'#'*70}")
            print(f"# CYCLE {i+1}/{cycles}")
            print(f"{'#'*70}")

            await self.run_cycle()

            if i < cycles - 1:
                print(f"⏳ Waiting {interval}s before next cycle...")
                await asyncio.sleep(interval)

        print(f"\n✅ Paper Trading completed!")
        print(f"💾 Results saved to: {self.results_file}")


async def main():
    agent = PaperTradingWithNeurons()

    # تشغيل 10 دورات، كل 5 دقائق
    await agent.run_continuous(cycles=10, interval=300)


if __name__ == "__main__":
    asyncio.run(main())
