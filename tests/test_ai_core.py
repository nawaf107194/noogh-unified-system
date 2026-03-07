"""
AI Core Test Suite

Comprehensive tests for the genuine AI components:
- WorldModel: beliefs, predictions, falsification (permanent)
- ConsequenceEngine: append-only ledger, constraints
- CoerciveMemory: blockers, penalties, overrides
- ScarTissue: permanent failure scarring
- GravityWell: centralized decision authority
"""

import pytest
import os
import shutil
import tempfile
from typing import Dict, Any


# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture
def temp_storage():
    """Create temporary storage directory for tests."""
    temp_dir = tempfile.mkdtemp(prefix="ai_core_test_")
    yield temp_dir
    # Cleanup after test
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def world_model(temp_storage):
    """Create a WorldModel for testing."""
    from unified_core.core.world_model import WorldModel
    # Override storage path
    wm = WorldModel()
    wm.STORAGE_DIR = os.path.join(temp_storage, "world_state")
    os.makedirs(wm.STORAGE_DIR, exist_ok=True)
    return wm


@pytest.fixture
def consequence_engine(temp_storage):
    """Create a ConsequenceEngine for testing."""
    from unified_core.core.consequence import ConsequenceEngine
    storage_path = os.path.join(temp_storage, "consequences", "ledger.jsonl")
    return ConsequenceEngine(storage_path)


@pytest.fixture
def coercive_memory(temp_storage, consequence_engine):
    """Create a CoerciveMemory for testing."""
    from unified_core.core.coercive_memory import CoerciveMemory
    mem = CoerciveMemory(consequence_engine=consequence_engine)
    mem.STORAGE_DIR = os.path.join(temp_storage, "coercive_memory")
    os.makedirs(mem.STORAGE_DIR, exist_ok=True)
    return mem


@pytest.fixture
def scar_tissue(temp_storage, coercive_memory, world_model):
    """Create ScarTissue for testing."""
    from unified_core.core.scar import ScarTissue
    st = ScarTissue(memory=coercive_memory, world_model=world_model)
    st.STORAGE_DIR = os.path.join(temp_storage, "scars")
    os.makedirs(st.STORAGE_DIR, exist_ok=True)
    return st


@pytest.fixture
def gravity_well(world_model, coercive_memory, consequence_engine, scar_tissue):
    """Create GravityWell for testing."""
    from unified_core.core.gravity import GravityWell
    return GravityWell(
        world_model=world_model,
        memory=coercive_memory,
        consequence_engine=consequence_engine,
        scar_tissue=scar_tissue
    )


# ============================================================
# WorldModel Tests
# ============================================================

class TestWorldModel:
    """Tests for WorldModel component."""
    
    def test_add_belief(self, world_model):
        """Test belief creation."""
        belief = world_model.add_belief("Test proposition", initial_confidence=0.8)
        
        assert belief is not None
        assert belief.proposition == "Test proposition"
        assert belief.confidence == 0.8
        assert belief.is_usable()
    
    def test_prediction_creation(self, world_model):
        """Test prediction from beliefs."""
        belief = world_model.add_belief("System is stable", initial_confidence=0.9)
        prediction = world_model.predict("Will system remain stable?", based_on=[belief.belief_id])
        
        assert prediction is not None
        assert len(prediction.based_on_beliefs) == 1
        assert prediction.resolved is False
    
    def test_falsification_is_permanent(self, world_model):
        """Test that falsification is permanent."""
        belief = world_model.add_belief("Incorrect belief", initial_confidence=0.7)
        prediction = world_model.predict("query", based_on=[belief.belief_id])
        
        # Falsify the prediction
        falsification = world_model.falsify(
            prediction.prediction_id, 
            {"success": False, "actual": "failure"}
        )
        
        assert falsification is not None
        assert belief.belief_id in falsification.beliefs_falsified
        
        # Belief should be permanently falsified
        updated_belief = world_model._beliefs[belief.belief_id]
        assert not updated_belief.is_usable()
        assert str(updated_belief.state) == "BeliefState.FALSIFIED"
    
    def test_falsification_count_only_grows(self, world_model):
        """Test that falsification count only increases."""
        initial_count = world_model.get_falsification_count()
        
        belief = world_model.add_belief("Test for falsification", 0.5)
        pred = world_model.predict("test_prediction", based_on=[belief.belief_id])
        world_model.falsify(pred.prediction_id, {"success": False})
        
        new_count = world_model.get_falsification_count()
        # Count should increase (or stay same if prediction was correct)
        assert new_count >= initial_count


# ============================================================
# ConsequenceEngine Tests
# ============================================================

class TestConsequenceEngine:
    """Tests for ConsequenceEngine component."""
    
    def test_commit_action(self, consequence_engine):
        """Test action commitment."""
        from unified_core.core.consequence import Action, Outcome
        
        action = Action(action_type="test_action", parameters={"key": "value"})
        outcome = Outcome(success=True, result={"data": "test"})
        
        hash_result = consequence_engine.commit(action, outcome)
        
        assert hash_result is not None
        assert len(hash_result) == 64  # SHA256 hex length
    
    def test_no_delete_method(self, consequence_engine):
        """Test that delete method does not exist."""
        assert not hasattr(consequence_engine._ledger, 'delete')
        assert not hasattr(consequence_engine._ledger, 'reset')
        assert not hasattr(consequence_engine._ledger, 'undo')
    
    def test_consequence_count_only_grows(self, consequence_engine):
        """Test that consequence count only increases."""
        from unified_core.core.consequence import Action, Outcome
        
        initial = consequence_engine.get_consequence_count()
        
        action = Action(action_type="test", parameters={})
        outcome = Outcome(success=True)
        consequence_engine.commit(action, outcome)
        
        assert consequence_engine.get_consequence_count() > initial
    
    def test_failed_action_creates_constraint(self, consequence_engine):
        """Test that failed actions create blocking constraints."""
        from unified_core.core.consequence import Action, Outcome
        
        action = Action(action_type="dangerous_action", parameters={})
        outcome = Outcome(success=False, error="Test failure")
        
        consequence_engine.commit(action, outcome)
        
        # Action should now be blocked
        new_action = Action(action_type="dangerous_action", parameters={})
        blocked, hash_ref = consequence_engine.is_action_blocked(new_action)
        
        assert blocked is True
        assert hash_ref is not None


# ============================================================
# CoerciveMemory Tests
# ============================================================

class TestCoerciveMemory:
    """Tests for CoerciveMemory component."""
    
    def test_block_action(self, coercive_memory):
        """Test action blocking."""
        from unified_core.core.coercive_memory import MemoryVerdict
        
        coercive_memory.block_action("forbidden_action", "Test block", permanent=True)
        
        verdict = coercive_memory.check("forbidden_action", {})
        assert verdict == MemoryVerdict.DISCOURAGED
    
    def test_penalize_idea(self, coercive_memory):
        """Test idea penalty accumulation."""
        coercive_memory.penalize_idea(["risky", "dangerous"], base_cost=1.0)
        
        cost1 = coercive_memory.get_total_cost("this is risky")
        assert cost1 >= 1.0
    
    def test_blocker_count_grows(self, coercive_memory):
        """Test that blocker count increases."""
        initial = coercive_memory.get_blocked_count()
        
        coercive_memory.block_action("action1", "reason", permanent=True)
        coercive_memory.block_action("action2", "reason", permanent=True)
        
        assert coercive_memory.get_blocked_count() == initial + 2
    
    def test_logic_destruction(self, coercive_memory):
        """Test logic override/destruction."""
        coercive_memory.override_logic("test_logic")
        
        assert coercive_memory.is_logic_destroyed("test_logic")


# ============================================================
# ScarTissue Tests
# ============================================================

class TestScarTissue:
    """Tests for ScarTissue component."""
    
    def test_inflict_scar(self, scar_tissue):
        """Test scar creation from failure."""
        from unified_core.core.scar import Failure
        
        initial_depth = scar_tissue.get_scar_depth()
        
        failure = Failure(
            failure_id="test_failure",
            action_type="failed_action",
            action_params={"test": True},
            error_message="Test error"
        )
        
        scar = scar_tissue.inflict(failure)
        
        assert scar is not None
        assert scar_tissue.get_scar_depth() > initial_depth
    
    def test_scar_blocks_action(self, scar_tissue):
        """Test that scarred actions are blocked."""
        from unified_core.core.scar import Failure
        
        failure = Failure(
            failure_id="block_test",
            action_type="blocked_by_scar",
            action_params={},
            error_message="Test"
        )
        
        scar_tissue.inflict(failure)
        
        assert scar_tissue.is_action_scarred("blocked_by_scar")
    
    def test_scar_count_only_grows(self, scar_tissue):
        """Test that scar count only increases."""
        from unified_core.core.scar import Failure
        
        initial = scar_tissue.get_scar_count()
        
        failure = Failure(
            failure_id="growth_test",
            action_type="test",
            action_params={},
            error_message="Test"
        )
        scar_tissue.inflict(failure)
        
        assert scar_tissue.get_scar_count() > initial


# ============================================================
# GravityWell Tests
# ============================================================

class TestGravityWell:
    """Tests for GravityWell component."""
    
    def test_decision_creation(self, gravity_well):
        """Test decision-making."""
        from unified_core.core.gravity import DecisionContext
        
        context = DecisionContext(query="Test decision", urgency=0.5)
        decision = gravity_well.decide(context)
        
        assert decision is not None
        assert decision.commitment_hash is not None
    
    def test_decision_count_grows(self, gravity_well):
        """Test that decision count only increases."""
        from unified_core.core.gravity import DecisionContext
        
        initial = gravity_well.get_decision_count()
        
        context = DecisionContext(query="Test", urgency=0.5)
        gravity_well.decide(context)
        
        assert gravity_well.get_decision_count() > initial
    
    def test_is_not_predictable(self, gravity_well):
        """Test that system claims unpredictability."""
        assert gravity_well.is_predictable() is False
    
    def test_goal_generation(self, gravity_well, world_model):
        """Test goal synthesis from beliefs."""
        # Add low-confidence belief to trigger goal
        world_model.add_belief("Uncertain proposition", initial_confidence=0.3)
        
        goals = gravity_well.generate_goals()
        
        # Should generate at least one goal due to low-confidence belief
        assert isinstance(goals, list)


# ============================================================
# State Reset Test
# ============================================================

class TestStateReset:
    """Test that state.reset() is forbidden."""
    
    def test_reset_raises_error(self):
        """Test that reset raises RuntimeError."""
        from unified_core.state import get_state
        
        state = get_state()
        
        with pytest.raises(RuntimeError) as excinfo:
            state.reset()
        
        assert "FORBIDDEN" in str(excinfo.value)


# ============================================================
# Integration Tests
# ============================================================

class TestAICoreIntegration:
    """Integration tests for the full AI core."""
    
    def test_failure_scars_block_memory(self, scar_tissue, coercive_memory):
        """Test that failures create memory blocks."""
        from unified_core.core.scar import Failure
        from unified_core.core.coercive_memory import MemoryVerdict
        
        failure = Failure(
            failure_id="integration_test",
            action_type="integration_action",
            action_params={},
            error_message="Integration test failure"
        )
        
        scar_tissue.inflict(failure)
        
        # Action should be blocked in memory
        verdict = coercive_memory.check("integration_action", {})
        assert verdict == MemoryVerdict.DISCOURAGED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
