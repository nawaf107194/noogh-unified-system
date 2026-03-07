#!/usr/bin/env python3
"""
Continuous Training Loop - حلقة تدريب مستمرة
1. RunPod يولد عصبونات معقدة
2. Paper Trading يختبرها
3. تحليل النتائج
4. إعادة التدريب مع RunPod
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from unified_core.runpod_brain import RunPodBrain
from agents.neuron_tester import NeuronTester
from agents.paper_trading_with_neurons import PaperTradingWithNeurons


class ContinuousTrainingLoop:
    def __init__(self):
        self.brain = RunPodBrain(
            base_url='https://6gylw7ox0y2qzd-8000.proxy.runpod.net',
            model='noogh-teacher'
        )
        self.neuron_tester = NeuronTester()
        self.paper_trader = None  # سيتم تهيئته لاحقاً

        self.data_file = Path('/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl')
        self.paper_trades_file = Path('/home/noogh/projects/noogh_unified_system/src/data/paper_trades_with_neurons.jsonl')
        self.training_log = Path('/home/noogh/projects/noogh_unified_system/src/data/training_log.jsonl')

    def load_historical_data(self):
        """تحميل البيانات التاريخية"""
        setups = []
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                for line in f:
                    setups.append(json.loads(line))
        return setups

    def load_paper_trades(self):
        """تحميل نتائج Paper Trading"""
        trades = []
        if self.paper_trades_file.exists():
            with open(self.paper_trades_file, 'r') as f:
                for line in f:
                    trades.append(json.loads(line))
        return trades

    def calculate_performance(self, setups):
        """حساب الأداء"""
        long_wins = len([s for s in setups if s['signal'] == 'LONG' and s.get('outcome') == 'WIN'])
        long_losses = len([s for s in setups if s['signal'] == 'LONG' and s.get('outcome') == 'LOSS'])
        short_wins = len([s for s in setups if s['signal'] == 'SHORT' and s.get('outcome') == 'WIN'])
        short_losses = len([s for s in setups if s['signal'] == 'SHORT' and s.get('outcome') == 'LOSS'])

        return {
            'total_setups': len(setups),
            'long': {'wins': long_wins, 'losses': long_losses},
            'short': {'wins': short_wins, 'losses': short_losses}
        }

    async def generate_new_neurons(self, iteration: int):
        """توليد عصبونات جديدة من RunPod"""
        print(f"\n{'='*70}")
        print(f"🧠 ITERATION {iteration}: Generating New Neurons")
        print(f"{'='*70}")

        # تحميل البيانات
        historical = self.load_historical_data()
        paper_trades = self.load_paper_trades()

        # دمج البيانات
        all_data = historical + paper_trades
        print(f"📊 Total data points: {len(all_data)}")
        print(f"   Historical: {len(historical)}")
        print(f"   Paper Trades: {len(paper_trades)}")

        # حساب الأداء
        perf = self.calculate_performance(all_data)

        # سياق يتحسن مع كل iteration
        context = f"""Iteration {iteration}. Focus on:
- Rejecting false signals (reduce losses)
- Multi-condition logic (3-4 conditions)
- Dynamic confidence scoring
- Avoid overfitting (test on unseen data)"""

        # توليد عصبونات
        result = await self.brain.analyze_and_generate_neurons(
            all_data[:100],  # عينة من البيانات
            perf,
            context
        )

        return result

    def test_neurons(self):
        """اختبار العصبونات المُولَّدة"""
        print(f"\n{'='*70}")
        print(f"🧪 TESTING: Testing Generated Neurons")
        print(f"{'='*70}")

        results = self.neuron_tester.test_all_neurons()
        best_neurons = self.neuron_tester.find_best_neurons(results)

        return results, best_neurons

    async def run_paper_trading(self, cycles: int = 5):
        """تشغيل Paper Trading"""
        print(f"\n{'='*70}")
        print(f"📈 PAPER TRADING: Running {cycles} cycles")
        print(f"{'='*70}")

        self.paper_trader = PaperTradingWithNeurons()
        await self.paper_trader.run_continuous(cycles=cycles, interval=180)  # 3 دقائق بين كل دورة

    def log_training_iteration(self, iteration: int, neuron_results: dict, best_neurons: list):
        """تسجيل iteration"""
        log_entry = {
            'iteration': iteration,
            'timestamp': datetime.now().isoformat(),
            'neurons_generated': len(neuron_results),
            'best_neurons': [
                {'name': name, 'improvement': score}
                for name, score in best_neurons[:3]
            ],
            'avg_improvement': sum(score for _, score in best_neurons[:3]) / min(3, len(best_neurons)) if best_neurons else 0
        }

        with open(self.training_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

        return log_entry

    async def run_training_loop(self, iterations: int = 3):
        """حلقة التدريب الرئيسية"""
        print(f"\n{'#'*70}")
        print(f"# CONTINUOUS TRAINING LOOP")
        print(f"# Iterations: {iterations}")
        print(f"{'#'*70}\n")

        for i in range(1, iterations + 1):
            print(f"\n\n{'█'*70}")
            print(f"█ ITERATION {i}/{iterations}")
            print(f"{'█'*70}\n")

            # 1. توليد عصبونات جديدة
            print(f"\n▶ Step 1: Generate Neurons")
            neuron_result = await self.generate_new_neurons(i)

            # 2. اختبار العصبونات
            print(f"\n▶ Step 2: Test Neurons")
            neuron_results, best_neurons = self.test_neurons()

            # 3. Paper Trading بالعصبونات الأفضل
            print(f"\n▶ Step 3: Paper Trading")
            await self.run_paper_trading(cycles=5)

            # 4. تسجيل النتائج
            print(f"\n▶ Step 4: Log Results")
            log = self.log_training_iteration(i, neuron_results, best_neurons)

            print(f"\n📊 Iteration {i} Summary:")
            print(f"   Neurons tested: {len(neuron_results)}")
            print(f"   Best improvement: {log['avg_improvement']:+.1f}%")
            if log['best_neurons']:
                print(f"   Top neuron: {log['best_neurons'][0]['name']} ({log['best_neurons'][0]['improvement']:+.1f}%)")

            # 5. انتظار قبل iteration التالي
            if i < iterations:
                wait_time = 300  # 5 دقائق
                print(f"\n⏳ Waiting {wait_time//60} minutes before next iteration...")
                await asyncio.sleep(wait_time)

        print(f"\n\n{'='*70}")
        print(f"✅ TRAINING LOOP COMPLETE!")
        print(f"{'='*70}")
        print(f"📊 Training log: {self.training_log}")
        print(f"💾 Paper trades: {self.paper_trades_file}")
        print(f"{'='*70}\n")


async def main():
    loop = ContinuousTrainingLoop()
    await loop.run_training_loop(iterations=3)


if __name__ == "__main__":
    asyncio.run(main())
