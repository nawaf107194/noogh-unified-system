import pytest
import asyncio
import time
import math
from unittest.mock import MagicMock, patch, AsyncMock
from unified_core.core.world_model import WorldModel, Belief
from unified_core.core.memory_store import UnifiedMemoryStore
from unified_core.core.scar import FailureRecord
from unified_core.core.meta_governor import MetaGovernor
from unified_core.agent_daemon import AgentDaemon

@pytest.mark.asyncio
async def test_cognitive_entropy_hysteresis():
    """Verify WorldModel Hysteresis (Schmitt Trigger) pruning."""
    wm = WorldModel()
    wm._memory = MagicMock()
    
    # Use LOCAL time to match WorldModel.consolidate_memory's time.mktime()
    now_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    
    # 1. Trigger Pruning (High Mass)
    mock_beliefs = {
        f"k{i}": {
            "belief_id": f"k{i}",
            "proposition": "test",
            "confidence": 0.9,
            "use_count": 100, 
            "last_used_at": now_str
        } for i in range(12)
    }
    wm._memory.get_all_beliefs.return_value = mock_beliefs
    
    wm._A_hi = 1000.0
    wm._A_lo = 800.0
    wm._lambda = 0.0001
    
    await wm.consolidate_memory()
    print(f"DEBUG: Active Mass={wm._active_mass}, Is Pruning={wm._is_pruning}")
    assert wm._is_pruning is True
    
    # 2. Stay in pruning until A_lo reached
    # Drop use_count so mass is 12 * 75 = 900
    for k in mock_beliefs:
        mock_beliefs[k]["use_count"] = 75
    await wm.consolidate_memory()
    print(f"DEBUG: Active Mass={wm._active_mass}, Is Pruning={wm._is_pruning}")
    assert wm._is_pruning is True # Still pruning (Mass = 900 > 800)
    
    # 3. Stop pruning (Mass = 12 * 50 = 600)
    for k in mock_beliefs:
        mock_beliefs[k]["use_count"] = 50
    await wm.consolidate_memory()
    print(f"DEBUG: Active Mass={wm._active_mass}, Is Pruning={wm._is_pruning}")
    assert wm._is_pruning is False # Stopped (Mass = 600 < 800)

@pytest.mark.asyncio
async def test_refined_healing_anti_gaming():
    """Verify FailureRecord Anti-Gaming and Rate Limiting."""
    fr = FailureRecord()
    fr._gpu_available = True
    fr._sacrificed_tensors = [MagicMock() for _ in range(10)]
    fr._total_sacrificed_mb = 500.0
    fr._total_depth = 5.0
    fr._heal_budget_mb = 200.0
    fr._last_heal_time = time.time() - 60
    
    # 1. Phantom Streak (No decision) -> Should NOT heal
    healed = await fr.heal(success_streak=20, decision_made=False, action_executed=True)
    assert healed == 0.0
    
    # 2. Valid Streak (Productive cycle) -> Should heal
    healed = await fr.heal(success_streak=20, decision_made=True, action_executed=True)
    assert healed >= 50.0
    assert fr._heal_budget_mb < 200.0

@pytest.mark.asyncio
async def test_predictive_governance_ladder():
    """Verify MetaGovernor Action Ladder escalation."""
    daemon = MagicMock()
    daemon.adjust_aggression = AsyncMock()
    daemon.adjust_interval = AsyncMock()
    daemon.recalibrate = AsyncMock()
    
    gov = MetaGovernor(agent_daemon=daemon)
    gov.world_model = MagicMock()
    gov.world_model._memory.get_all_falsifications = MagicMock(return_value=[])
    
    # Start stable
    await gov.evaluate_performance()
    assert gov.ladder_level == 0
    
    # Trip instability
    gov.world_model._memory.get_all_falsifications.return_value = [{"id": i} for i in range(5)]
    await gov.evaluate_performance()
    assert gov.ladder_level == 1
    
    gov.world_model._memory.get_all_falsifications.return_value = [{"id": i} for i in range(15)]
    await gov.evaluate_performance()
    assert gov.ladder_level == 2
    daemon.adjust_interval.assert_called()

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
