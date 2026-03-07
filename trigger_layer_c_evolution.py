#!/usr/bin/env python3
import asyncio
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/home/noogh/projects/noogh_unified_system/src/.env")

from unified_core.runpod_brain import RunPodBrainEvolver, EvolutionConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FirstEvolution")

async def main():
    logger.info("🚀 Starting Layer C: Genetic Evolution Engine (RunPodBrainEvolver)")
    
    # Load historical data 
    # We will use the backtest_setups.jsonl as our reference for historical market data
    history_file = Path("/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl")
    
    historical_data = []
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                historical_data.append(json.loads(line))
                
    # Keep only the last 150 setups for recent context to the model
    historical_data = historical_data[-150:]
    
    logger.info(f"Loaded {len(historical_data)} recent setups for market context.")

    # Initialize the evolver with RunPod settings
    evo_config = EvolutionConfig(
        consensus_n=3,
        mutation_strength="high", # First generation: encourage wider exploration because we have strong Layer B protection
        parents_k=2 # Initial, manifest is probably empty, it will handle it natively
    )
    
    evolver = RunPodBrainEvolver(
        evo=evo_config
    )
    
    # Run the evolution round
    logger.info("🧬 Triggering evolve_round()...")
    result = await evolver.evolve_round(
        historical_data=historical_data,
        context="First generation inside Layer C. We have a robust Statistical Filter (Layer B) in place with Expectancy 0.10. Therefore, you must focus purely on enhancing precision logic. Don't worry about being too protective, find aggressive alpha."
    )
    
    logger.info("🟢 Evolution Round Complete!")
    logger.info(json.dumps(result, indent=2))
    
    await evolver.aclose()

if __name__ == "__main__":
    asyncio.run(main())
