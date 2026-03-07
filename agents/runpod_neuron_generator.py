#!/usr/bin/env python3
"""
RunPod Neuron Generator (vLLM version)
"""

import sys
import json
import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))
from unified_core.runpod_brain import RunPodBrain

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class RunPodNeuronGenerator:
    def __init__(self):
        self.brain = RunPodBrain()
        self.data_file = Path('/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl')

    def load_historical_data(self) -> List[Dict]:
        setups = []
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                for line in f:
                    setups.append(json.loads(line))
        return setups

    def calculate_current_performance(self, setups: List[Dict]) -> Dict:
        long_wins = len([s for s in setups if s['signal'] == 'LONG' and s['outcome'] == 'WIN'])
        long_losses = len([s for s in setups if s['signal'] == 'LONG' and s['outcome'] == 'LOSS'])
        short_wins = len([s for s in setups if s['signal'] == 'SHORT' and s['outcome'] == 'WIN'])
        short_losses = len([s for s in setups if s['signal'] == 'SHORT' and s['outcome'] == 'LOSS'])

        return {
            'total_setups': len(setups),
            'long': {'wins': long_wins, 'losses': long_losses},
            'short': {'wins': short_wins, 'losses': short_losses}
        }

    async def generate_neurons(self):
        setups = self.load_historical_data()
        if not setups:
            logger.error("❌ No data found")
            return

        # Use small sample for fast RunPod response (Cloudflare timeout limit)
        import random
        sample_size = min(20, len(setups))  # Reduced from 100 to 20
        setups_sample = random.sample(setups, sample_size)
        logger.info(f"📊 Using {sample_size} sample setups (from {len(setups)} total)")

        current_perf = self.calculate_current_performance(setups)  # Use all for stats
        context = "نحتاج عصبونات تركز على زيادة دقة التصنيف بين الصفقات الرابحة والخاسرة."

        await self.brain.analyze_and_generate_neurons(setups_sample, current_perf, context)

async def main():
    if not os.getenv('RUNPOD_BASE_URL'):
        print("\n⚠️  مطلوب تعيين رابط הـ Pod الخاص بك")
        print("export RUNPOD_BASE_URL='https://<POD_ID>-8000.proxy.runpod.net'")
        return

    generator = RunPodNeuronGenerator()
    await generator.generate_neurons()

if __name__ == "__main__":
    asyncio.run(main())
