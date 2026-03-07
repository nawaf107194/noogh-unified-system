"""
Scar Enforcement Tests

Verifies that FailureRecord with enable_enforcement=True
actually blocks actions through is_action_blocked().
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestScarEnforcement:
    """Test suite for scar enforcement functionality."""
    
    def test_enforcement_enabled_by_default(self):
        """FailureRecord should have enforcement enabled by default."""
        from unified_core.core.scar import FailureRecord
        
        fr = FailureRecord()
        assert fr._enable_enforcement is True, "Enforcement should be enabled by default"
    
    def test_enforcement_can_be_disabled(self):
        """FailureRecord should allow disabling enforcement."""
        from unified_core.core.scar import FailureRecord
        
        fr = FailureRecord(enable_enforcement=False)
        assert fr._enable_enforcement is False
    
    def test_is_action_blocked_method_exists(self):
        """FailureRecord should have is_action_blocked method."""
        from unified_core.core.scar import FailureRecord
        
        fr = FailureRecord()
        assert hasattr(fr, 'is_action_blocked')
        assert callable(fr.is_action_blocked)
    
    def test_is_action_blocked_returns_false_for_unknown_action(self):
        """Unknown actions should not be blocked."""
        from unified_core.core.scar import FailureRecord
        
        fr = FailureRecord(enable_enforcement=True)
        assert fr.is_action_blocked("unknown_action_xyz") is False
    
    def test_is_action_blocked_returns_false_when_enforcement_disabled(self):
        """With enforcement disabled, is_action_blocked should always return False."""
        from unified_core.core.scar import FailureRecord, Failure
        import hashlib
        import time
        
        fr = FailureRecord(enable_enforcement=False)
        
        # Inflict a scar
        failure = Failure(
            failure_id=hashlib.sha256(f"test:{time.time()}".encode()).hexdigest()[:16],
            action_type="test_action",
            action_params={},
            error_message="Test failure"
        )
        fr.inflict(failure)
        
        # Even with scar, enforcement disabled means not blocked
        assert fr.is_action_blocked("test_action") is False
    
    def test_is_action_blocked_returns_true_when_enforced(self):
        """With enforcement enabled, scarred actions should be blocked."""
        from unified_core.core.scar import FailureRecord, Failure
        import hashlib
        import time
        
        fr = FailureRecord(enable_enforcement=True)
        
        # Inflict a scar
        failure = Failure(
            failure_id=hashlib.sha256(f"test:{time.time()}".encode()).hexdigest()[:16],
            action_type="blocked_action",
            action_params={},
            error_message="Test failure"
        )
        fr.inflict(failure)
        
        # With enforcement enabled, action should be blocked
        assert fr.is_action_blocked("blocked_action") is True
    
    def test_is_action_scarred_returns_true_regardless_of_enforcement(self):
        """is_action_scarred should return True even if enforcement is disabled."""
        from unified_core.core.scar import FailureRecord, Failure
        import hashlib
        import time
        
        fr = FailureRecord(enable_enforcement=False)
        
        # Inflict a scar
        failure = Failure(
            failure_id=hashlib.sha256(f"test:{time.time()}".encode()).hexdigest()[:16],
            action_type="scarred_action",
            action_params={},
            error_message="Test failure"
        )
        fr.inflict(failure)
        
        # is_action_scarred should still return True
        # (it's a record, not an enforcement check)
        assert fr.is_action_scarred("scarred_action") is True


class TestGravityWellScarIntegration:
    """Test that DecisionScorer respects scar enforcement."""
    
    def test_gravity_well_uses_is_action_blocked(self):
        """DecisionScorer should use is_action_blocked, not is_action_scarred."""
        import inspect
        from unified_core.core.gravity import DecisionScorer
        
        # Get the source of the decide method
        source = inspect.getsource(DecisionScorer.decide)
        
        # Should use is_action_blocked for enforcement
        assert "is_action_blocked" in source, "DecisionScorer.decide should use is_action_blocked"


class TestDreamerIntegration:
    """Test Dreamer integration in AgentDaemon."""
    
    def test_dreamer_attribute_exists_in_agent_daemon(self):
        """AgentDaemon should have _dreamer attribute."""
        import inspect
        from unified_core.agent_daemon import AgentDaemon
        
        source = inspect.getsource(AgentDaemon.__init__)
        assert "_dreamer" in source, "AgentDaemon should initialize _dreamer"
    
    def test_synthesize_goals_method_exists(self):
        """AgentDaemon should have _synthesize_goals method."""
        from unified_core.agent_daemon import AgentDaemon
        
        assert hasattr(AgentDaemon, '_synthesize_goals')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
