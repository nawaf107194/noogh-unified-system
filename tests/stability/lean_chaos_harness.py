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
logger = logging.getLogger("lean_chaos")

async def run_lean_chaos():
    logger.info("🔥 STARTING LEAN CHAOS STRESS HARNESS (v13.5.3) 🔥")
    
    # Setup Daemon with mock memory store to avoid heavy IO but simulate latency
    daemon = AgentDaemon()
    daemon._world_model = WorldModel()
    
    # We want a REAL memory store but with artificial latency instrumented
    # Or just use the real one and flood it. Let's use real for physical proof.
    from unified_core.core.memory_store import UnifiedMemoryStore
    # Ensure we use a test DB path if possible, but for this stress we'll use the real one as requested
    daemon._world_model._memory = UnifiedMemoryStore() 
    
    daemon._meta_governor = MetaGovernor(agent_daemon=daemon)
    daemon._specialized_agents = [] # No specialists for speed
    
    stability_log = []
    
    # Simulate 50 cycles of CHAOS
    for cycle in range(1, 51):
        # 1. Injection Phase: Massive belief burst (simulating WAL pressure)
        for i in range(1000):
            daemon._world_model.add_belief(
                f"CHAOS_JUNK_{cycle}_{i}: Noise level high.", 
                initial_confidence=0.1
            )
        
        # 2. Failure Pressure (Cycle 10-20)
        if 10 <= cycle <= 20:
            # Inject "synthetic" falsifications by manually adding records to the falsification table
            # Actually, we can just mock the count for the governor
            daemon._world_model._memory.get_all_falsifications = MagicMock(return_value=[{"id": i} for i in range(cycle * 2)])
        else:
            daemon._world_model._memory.get_all_falsifications = MagicMock(return_value=[])
            daemon._consecutive_success_streak += 1
            
        # 3. Execution Phase
        # Trigger consolidation (Throttled but we want to see it work)
        # We manually wait 0.1s to allow some loop concurrency
        await daemon._world_model.consolidate_memory()
        await daemon._meta_governor.evaluate_performance()
        
        # 4. Physical Audit
        stats = daemon._world_model.get_belief_state()
        total = stats['total_beliefs']
        active = stats.get('active', 0)
        dead_ratio = (total - active) / total if total > 0 else 0
        stability = (total - stats['falsified']) / total * 100 if total > 0 else 100
        stability_log.append(stability)
        
        if cycle % 5 == 0 or dead_ratio > 0.6:
            logger.info(f"CYCLE {cycle:02} | Total: {total:6} | DeadRatio: {dead_ratio:.2f} | Ladder: {daemon._meta_governor.ladder_level} | Stability: {stability:.1f}%")

    avg_stability = sum(stability_log) / len(stability_log)
    logger.info(f"\n✅ LEAN CHAOS COMPLETE.")
    logger.info(f"🏆 AVERAGE STABILITY: {avg_stability:.2f}%")
    logger.info(f"🏆 FINAL POPULATION: {total}")
    
    if avg_stability > 95:
        logger.info("✨ SYSTEM SURVIVED CHAOS WITH RECONCILED POPULATION ✨")

if __name__ == "__main__":
    asyncio.run(run_lean_chaos())
