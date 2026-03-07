import asyncio
import sys
import os
import logging

# Setup path
sys.path.append("/home/noogh/projects/noogh_unified_system/src")

from unified_core.core.world_model import WorldModel, Observation
from unified_core.core.memory_store import UnifiedMemoryStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_updates")

async def test_world_model():
    logger.info("Starting WorldModel verification...")
    wm = WorldModel()
    await wm.setup()
    
    # 1. Test get_belief_state
    logger.info("Testing get_belief_state...")
    state = await wm.get_belief_state()
    required_keys = [
        "total_beliefs", "active", "weakened", "falsified", 
        "average_confidence", "total_falsifications", 
        "background_tasks", "loaded"
    ]
    for key in required_keys:
        assert key in state, f"Missing key: {key}"
    logger.info("✅ get_belief_state verified")
    
    # 2. Test get_recent_observations
    logger.info("Testing get_recent_observations...")
    obs = await wm.get_recent_observations(limit=5)
    assert isinstance(obs, list), "Should return a list"
    logger.info(f"✅ get_recent_observations verified (found {len(obs)})")
    
    # 3. Test evolution tracking
    logger.info("Testing evolution tracking...")
    evol_id = "test_evol_123"
    await wm.record_evolution_step(
        evolution_id=evol_id,
        path="Verification",
        eye="Stability",
        rationale="Testing code updates",
        context={"test": True},
        outcome="Success",
        success=True
    )
    
    history = await wm.get_evolution_history(limit=5)
    found = False
    for item in history:
        if item["evolution_id"] == evol_id:
            found = True
            break
    assert found, "Evolution step not found in history"
    logger.info("✅ Evolution tracking verified")
    
    # 4. Test query latency (Sync)
    logger.info("Testing get_query_latency...")
    latency = wm.get_query_latency()
    assert isinstance(latency, float), "Latency should be a float"
    logger.info(f"✅ get_query_latency verified: {latency}")
    
    # 5. Test consolidate_memory
    logger.info("Testing consolidate_memory...")
    await wm.consolidate_memory()
    logger.info("✅ consolidate_memory verified (completed without error)")

    await wm.shutdown()
    logger.info("All verifications PASSED")

if __name__ == "__main__":
    asyncio.run(test_world_model())
