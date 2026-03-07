import asyncio
import time
import logging
from unified_core.agent_daemon import AgentDaemon
from unified_core.core.world_model import WorldModel
from unified_core.core.meta_governor import MetaGovernor

# Setup minimal logging to see the "wow" effects
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("stress_test")

async def run_stress_test():
    logger.info("🚀 INITIALIZING MATHEMATICAL HARDENING STRESS TEST (v13.5.2)...")
    
    daemon = AgentDaemon()
    await daemon.initialize()
    
    stability_scores = []
    
    # Simulate 30 cycles
    for cycle in range(1, 31):
        logger.info(f"\n--- CYCLE {cycle} ---")
        
        # 1. Simulate Cognitive Bloat (Add random beliefs)
        for i in range(10):
            daemon._world_model.add_belief(f"STRESS_LOG_{cycle}_{i}: System entropy is nominal.", initial_confidence=0.9)
        
        # 2. Simulate Periodic Failure Injection (Cycles 10-15)
        if 10 <= cycle <= 15:
            logger.warning(f"  [STRESS] Injecting artificial failure...")
            # Mocking a falsification
            from unified_core.core.world_model import Observation
            daemon._world_model.observe(Observation(source="STRESS_ENV", content={"type": "error", "message": "Simulated drift"}))
            # Manually trigger a scar to test FGDT (Failure Gradient)
            daemon._consecutive_failures += 1
            daemon._success_count = 0
            daemon._consecutive_success_streak = 0
            # Force a governor audit
            await daemon._meta_governor.evaluate_performance()
        else:
            # Successful cycle
            daemon._consecutive_success_streak += 1
            daemon._success_count += 1
            # Heal
            await daemon._scar_tissue.heal(
                success_streak=daemon._consecutive_success_streak,
                decision_made=True,
                action_executed=True
            )
        
        # 3. Consolidation
        await daemon._world_model.consolidate_memory()
        
        # 4. Record stability (Sample ratio of usable vs total)
        stats = daemon._world_model.get_belief_state()
        total = stats['total_beliefs']
        if total > 0:
            stability = (total - stats['falsified']) / total * 100
            stability_scores.append(stability)
            logger.info(f"📊 STABILITY SCORE: {stability:.2f}% | Active Mass: {daemon._world_model._active_mass:.1f} | Ladder: {daemon._meta_governor.ladder_level}")

    # Final Verdict
    avg_stability = sum(stability_scores) / len(stability_scores)
    logger.info(f"\n✅ STRESS TEST COMPLETE.")
    logger.info(f"🏆 FINAL STABILITY VERDICT: {avg_stability:.2f}/100")
    
    if avg_stability > 95:
        logger.info("✨ SYSTEM ATTAINED MATHEMATICAL HARDENING (v13.5.2) ✨")
    
    await daemon.shutdown()

if __name__ == "__main__":
    asyncio.run(run_stress_test())
