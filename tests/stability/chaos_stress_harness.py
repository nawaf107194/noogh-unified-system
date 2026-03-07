import asyncio
import time
import random
import logging
from concurrent.futures import ThreadPoolExecutor
from unified_core.agent_daemon import AgentDaemon
from unified_core.core.world_model import WorldModel, Observation
from unified_core.core.meta_governor import MetaGovernor

# Setup aggressive logging to see the "chaos"
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s')
logger = logging.getLogger("chaos_harness")

async def simulate_io_pressure(db_op_func, *args, **kwargs):
    """Adds artificial delay to mock I/O pressure/slow disk."""
    await asyncio.sleep(random.uniform(0.01, 0.05)) # 10-50ms lag
    return await asyncio.to_thread(db_op_func, *args, **kwargs)

async def belief_flooder(daemon, count_per_burst):
    """Injects massive amounts of junk beliefs to force bloat."""
    for i in range(count_per_burst):
        daemon._world_model.add_belief(
            f"CHAOS_JUNK_{time.time()}_{i}: Entropy is high but utility is zero.",
            initial_confidence=random.uniform(0.1, 0.4)
        )
    logger.info(f"💣 FLOODER: Injected {count_per_burst} beliefs.")

async def contention_worker(daemon):
    """Reads and writes concurrently to stress SQLite locks."""
    for _ in range(50):
        try:
            # Random read
            daemon._world_model.get_belief_state()
            # Random write
            daemon._world_model.add_belief("Stress locking belief.", initial_confidence=0.5)
            await asyncio.sleep(0.001)
        except Exception as e:
            logger.error(f"💥 CONTENTION ERROR: {e}")

async def run_chaos_stress():
    logger.info("🔥 STARTING CHAOS STRESS HARNESS (v13.5.3) 🔥")
    
    daemon = AgentDaemon()
    await daemon.initialize()
    
    # 0. Preparation: Reset memory to known state if needed
    # (Using existing memory store, but we monitor growth)
    
    stability_log = []
    
    # Simulate 50 cycles of PURE CHAOS
    for cycle in range(1, 51):
        logger.info(f"\n⚡ CHAOS CYCLE {cycle} ⚡")
        
        # 1. Start parallel chaos workers
        flooder_task = asyncio.create_task(belief_flooder(daemon, 1000)) # 1k per cycle
        contention_tasks = [asyncio.create_task(contention_worker(daemon)) for _ in range(3)]
        
        # 2. Failure Injection (Cycle 20-30: Massive Failure Burst)
        if 20 <= cycle <= 30:
            logger.critical("🚨 INJECTING SYSTEMIC FAILURE BURST (FGDT STRESS)...")
            daemon._world_model.observe(Observation(source="CHAOS_ENGINE", content={"type": "critical_corruption", "severity": 0.9}))
            daemon._consecutive_failures += 5
            daemon._consecutive_success_streak = 0
            await daemon._meta_governor.evaluate_performance()
        else:
            # Recovery streaks
            daemon._consecutive_success_streak += 1
            daemon._success_count += 1
            await daemon._scar_tissue.heal(
                success_streak=daemon._consecutive_success_streak,
                decision_made=True,
                action_executed=True
            )
            
        # 3. Force Consolidation
        # Note: Throttling will skip if called too fast (<5s)
        await daemon._world_model.consolidate_memory()
        
        # 4. Maintenance Specialist Audit
        await daemon._maintenance_specialist.perform_scheduled_maintenance(cycle)
        
        # 5. Wait for cycle workers to wrap up
        await asyncio.gather(flooder_task, *contention_tasks)
        
        # 6. Physical Audit
        stats = daemon._world_model.get_belief_state()
        total = stats['total_beliefs']
        active = stats.get('active', 0)
        falsified = stats['falsified']
        
        dead_ratio = (total - active) / total if total > 0 else 0
        stability = (total - falsified) / total * 100 if total > 0 else 100
        stability_log.append(stability)
        
        logger.info(f"📊 STATS: Total={total} | DeadRatio={dead_ratio:.2f} | Ladder={daemon._meta_governor.ladder_level}")
        logger.info(f"📉 STABILITY: {stability:.2f}% | Latency EWMA: {daemon._world_model._memory._query_latency_ewma:.3f}s")

    # FINAL REPORT
    avg_stability = sum(stability_log) / len(stability_log)
    logger.info(f"\n🏁 CHAOS HARNESS COMPLETE.")
    logger.info(f"🏁 AVERAGE STABILITY: {avg_stability:.2f}/100")
    
    if avg_stability > 95 and total < 20000: # Bounded growth check
        logger.info("🚀 SYSTEM SURVIVED THE CHAOS. MATHEMATICAL HARDENING IS FULLY RECONCILED. 🚀")
    else:
        logger.error("❌ SYSTEM FAILED TO CONTAIN THE BLOAT OR STABILIZE.")

    await daemon.shutdown()

if __name__ == "__main__":
    asyncio.run(run_chaos_stress())
