import asyncio
import time
import random
import math
import logging
from unittest.mock import MagicMock, AsyncMock
from unified_core.core.world_model import WorldModel, Observation
from unified_core.core.meta_governor import MetaGovernor
from unified_core.agent_daemon import AgentDaemon

# Setup minimal logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("chaos_2_0")

async def run_pressure_scaling():
    logger.info("🔥 STARTING CHAOS 2.0: PRESSURE SCALING HARNESS (v13.5.4) 🔥")
    
    daemon = AgentDaemon()
    daemon._world_model = WorldModel()
    
    # Use real memory store but monitor file growth
    from unified_core.core.memory_store import UnifiedMemoryStore
    daemon._world_model._memory = UnifiedMemoryStore()
    
    daemon._meta_governor = MetaGovernor(agent_daemon=daemon)
    daemon._specialized_agents = [] # Keep it lean
    
    stability_log = []
    
    # TARGET: Reach 50,000 beliefs and observe the "Wall Effect"
    logger.info("⚡ PHASE 1: PRE-SURGE (Injecting 10k base noise)...")
    for i in range(10):
        for j in range(1000):
            # Realistic Noise: use_count=0, confidence < 0.2
            daemon._world_model.add_belief(
                f"NOISE_{i}_{j}: Background cognitive hum.", 
                initial_confidence=random.uniform(0.01, 0.15)
            )
        await daemon._world_model.consolidate_memory()
    
    total_cycles = 60
    logger.info(f"⚡ PHASE 2: CHAOS SURGE (Injecting 2k per cycle)...")
    
    for cycle in range(1, total_cycles + 1):
        # 1. Injection Burst
        for i in range(2000):
            daemon._world_model.add_belief(
                f"SURGE_{cycle}_{i}: Extreme cognitive pressure.",
                initial_confidence=random.uniform(0.01, 0.1)
            )
        
        # 2. Execution & Consolidation
        start_time = time.time()
        # Ensure we await or allow loop cycle for the task
        await daemon._world_model.consolidate_memory()
        # Small sleep to ensure async IO tasks in prune can start
        await asyncio.sleep(0.001) 
        latency = time.time() - start_time
        
        await daemon._meta_governor.evaluate_performance()
        
        # 3. Telemetry
        stats = daemon._world_model.get_belief_state()
        total = stats['total_beliefs']
        active = stats.get('active', 0)
        dead_ratio = (total - active) / total if total > 0 else 0
        
        # Stability = Performance Stability (based on latency variance)
        perf_stability = 100 / (1 + latency)
        stability_log.append(perf_stability)
        
        if cycle % 5 == 0 or total > 48000:
            logger.info(f"CYCLE {cycle:02} | Total: {total:6} | DeadRatio: {dead_ratio:.2f} | Latency: {latency:.3f}s | PerfScore: {perf_stability:.1f}%")
        
        # Stop check
        if total > 60000:
             logger.error("❌ FAILED: System exceeded HARD_CAP (60k+). Pruning too slow.")
             break

    avg_perf = sum(stability_log) / len(stability_log)
    logger.info(f"\n✅ CHAOS 2.0 COMPLETE.")
    logger.info(f"🏆 AVERAGE PERFORMANCE STABILITY: {avg_perf:.2f}%")
    logger.info(f"🏆 FINAL POPULATION: {total}")
    
    if total <= 55000: # Allow some buffer for the burst cycle
        logger.info("✨ SYSTEM SURVIVED THE WALL. PHYSICAL BOUNDS ENFORCED. ✨")
    else:
        logger.error("❌ SYSTEM COLLAPSED UNDER THE BOLAT.")

if __name__ == "__main__":
    asyncio.run(run_pressure_scaling())
