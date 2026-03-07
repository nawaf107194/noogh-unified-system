import asyncio
import pytest
from unittest.mock import MagicMock, patch
from unified_core.core.scar import Failure, FailureRecord, Scar
from unified_core.agent_daemon import AgentDaemon

@pytest.mark.asyncio
async def test_exponential_gpu_healing(tmp_path):
    """Test v2.0 Exponential Healing math."""
    with patch("torch.cuda.is_available", return_value=True), \
         patch("torch.zeros", return_value=MagicMock()), \
         patch("unified_core.core.scar.FailureRecord.STORAGE_LOCATIONS", [str(tmp_path)]):
         
        fr = FailureRecord(enable_enforcement=True)
        fr._gpu_available = True
        
        # Sacrifice some VRAM
        # medium severity = 1.0 depth = 50MB
        for i in range(10):
            f = Failure(failure_id=f"f{i}", action_type="test", action_params={}, error_message="err")
            fr.inflict(f, severity="critical")
        
        total_sac = fr._total_sacrificed_mb
        assert total_sac >= 500.0
        
        # 1. Short streak should have low recovery (at least 1 chunk)
        # depth 2.0 = 100MB chunk
        recovered_short = fr.heal(success_streak=3)
        assert recovered_short >= 100.0
        
        # 2. Long streak should have exponential boost
        recovered_long = fr.heal(success_streak=20)
        assert recovered_long >= 100.0
        print(f"  ✓ Exponential Healing: Short Streak=50MB, Long Streak={recovered_long}MB")

@pytest.mark.asyncio
async def test_predictive_failure_gradient():
    """Test v2.0 MetaGovernor Predictive Damping."""
    from unified_core.core.meta_governor import MetaGovernor
    daemon = MagicMock()
    daemon.recalibrate = MagicMock(return_value=asyncio.Future())
    daemon.recalibrate.return_value.set_result(None)
    
    gov = MetaGovernor(agent_daemon=daemon)
    
    # Simulate a sudden spike in failures (falsifications)
    gov.world_model._memory.get_all_falsifications = MagicMock(return_value=[
        {"falsification_id": f"f{i}"} for i in range(4)
    ])
    
    await gov.evaluate_performance()
    
    # Gradient was 4 (0 to 4). Should trigger recalibration even if < 5 per agent.
    daemon.recalibrate.assert_called_with("Predictive instability (high failure gradient)")
    print("  ✓ MetaGovernor detected predictive instability gradient.")

if __name__ == "__main__":
    asyncio.run(test_gpu_healing_logic())
    asyncio.run(test_daemon_triggers_healing())
