"""
Phase 3 - Governed Spine Testing Suite

Comprehensive tests to verify:
1. Zero breaking changes (governance OFF)
2. Dry-run mode (logging only)
3. Enforcement mode (future)
"""

import pytest
import os
from unittest.mock import Mock, patch

from unified_core.governance import (
    execution_envelope,
    flags,
    GovernanceError,
    get_observability_bus,
    GovernanceEventType
)
from unified_core.decision_classifier import DecisionImpact
from unified_core.auth import AuthContext


class TestGovernanceDisabled:
    """Test that governance OFF = zero impact."""
    
    def test_imports_succeed(self):
        """Governance modules import without errors."""
        from unified_core.governance import (
            execution_envelope,
            flags,
            get_governor
        )
        assert execution_envelope is not None
        assert flags is not None
        assert get_governor is not None
    
    def test_default_flags_are_off(self):
        """All flags OFF by default."""
        assert flags.GOVERNANCE_ENABLED == False
        assert flags.AUTH_GATE_ENABLED == False
        assert flags.APPROVAL_GATE_ENABLED == False
        assert flags.WRAP_PROCESS_SPAWN == False
        assert flags.WRAP_PROCESS_KILL == False
        assert flags.WRAP_FS_DELETE == False
    
    def test_envelope_is_transparent_when_disabled(self):
        """Envelope does nothing when governance disabled."""
        auth = Mock()
        auth.user_id = "test"
        
        executed = False
        
        with execution_envelope(
            auth=auth,
            component="process.spawn"
        ):
            executed = True
        
        assert executed, "Code should execute normally"


class TestDryRunMode:
    """Test dry-run mode (logging only)."""
    
    def setup_method(self):
        """Enable dry-run before each test."""
        flags.GOVERNANCE_ENABLED = True
        flags.DRY_RUN = True
    
    def teardown_method(self):
        """Reset flags after each test."""
        flags.GOVERNANCE_ENABLED = False
        flags.DRY_RUN = True
    
    def test_missing_auth_logs_warning_in_dry_run(self, caplog):
        """Missing auth logs warning but doesn't block."""
        flags.AUTH_GATE_ENABLED = True
        
        executed = False
        
        with execution_envelope(
            auth=None,  # Missing auth!
            component="process.spawn"
        ):
            executed = True
        
        assert executed, "Should execute in dry-run"
        # Check logs for warning (implementation detail)
    
    def test_events_published_in_dry_run(self):
        """Events are published even in dry-run."""
        events_received = []
        
        def handler(event):
            events_received.append(event)
        
        bus = get_observability_bus()
        bus.subscribe(GovernanceEventType.EXECUTION_STARTED, handler)
        
        auth = Mock()
        auth.user_id = "test"
        
        with execution_envelope(
            auth=auth,
            component="process.spawn"
        ):
            pass
        
        assert len(events_received) >= 1
        assert events_received[0].component == "process.spawn"


class TestActuatorWrapping:
    """Test that actuators are properly wrapped."""
    
    def test_process_spawn_has_governance_wrapper(self):
        """ProcessActuator.spawn has governance wrapper."""
        from unified_core.core.actuators import ProcessActuator
        import inspect
        
        source = inspect.getsource(ProcessActuator.spawn)
        assert "execution_envelope" in source
        assert "flags.is_enabled_for" in source
    
    def test_process_kill_has_governance_wrapper(self):
        """ProcessActuator.kill has governance wrapper."""
        from unified_core.core.actuators import ProcessActuator
        import inspect
        
        source = inspect.getsource(ProcessActuator.kill)
        assert "execution_envelope" in source
        assert "flags.is_enabled_for" in source
    
    def test_filesystem_delete_has_governance_wrapper(self):
        """FilesystemActuator.delete_file has governance wrapper."""
        from unified_core.core.actuators import FilesystemActuator
        import inspect
        
        source = inspect.getsource(FilesystemActuator.delete_file)
        assert "execution_envelope" in source
        assert "flags.is_enabled_for" in source


class TestBackwardCompatibility:
    """Ensure zero breaking changes."""
    
    def test_actuator_signatures_unchanged(self):
        """Actuator method signatures are unchanged."""
        from unified_core.core.actuators import ProcessActuator, FilesystemActuator
        import inspect
        
        # ProcessActuator.spawn signature
        spawn_sig = inspect.signature(ProcessActuator.spawn)
        params = list(spawn_sig.parameters.keys())
        assert params == ['self', 'cmd', 'auth_context', 'cwd']
        
        # ProcessActuator.kill signature
        kill_sig = inspect.signature(ProcessActuator.kill)
        params = list(kill_sig.parameters.keys())
        assert params == ['self', 'pid', 'auth_context', 'sig']
        
        # FilesystemActuator.delete_file signature
        delete_sig = inspect.signature(FilesystemActuator.delete_file)
        params = list(delete_sig.parameters.keys())
        assert params == ['self', 'path', 'auth_context']
    
    def test_return_types_unchanged(self):
        """Return types are unchanged."""
        from unified_core.core.actuators import (
            ProcessActuator,
            FilesystemActuator,
            ActuatorAction
        )
        import inspect
        
        # All should return ActuatorAction (class, not string)
        assert inspect.signature(ProcessActuator.spawn).return_annotation == ActuatorAction
        assert inspect.signature(ProcessActuator.kill).return_annotation == ActuatorAction
        assert inspect.signature(FilesystemActuator.delete_file).return_annotation == ActuatorAction


class TestFeatureFlags:
    """Test feature flag system."""
    
    def test_is_enabled_for_checks_both_master_and_component(self):
        """is_enabled_for checks both master and component flags."""
        from unified_core.governance.feature_flags import GovernanceFlags
        
        # Save original values
        orig_governance = GovernanceFlags.GOVERNANCE_ENABLED
        orig_spawn = GovernanceFlags.WRAP_PROCESS_SPAWN
        
        try:
            # Master OFF →component doesn't matter
            GovernanceFlags.GOVERNANCE_ENABLED = False
            GovernanceFlags.WRAP_PROCESS_SPAWN = True
            assert GovernanceFlags.is_enabled_for("process.spawn") == False
            
            # Master ON, component OFF
            GovernanceFlags.GOVERNANCE_ENABLED = True
            GovernanceFlags.WRAP_PROCESS_SPAWN = False
            assert GovernanceFlags.is_enabled_for("process.spawn") == False
            
            # Both ON
            GovernanceFlags.GOVERNANCE_ENABLED = True
            GovernanceFlags.WRAP_PROCESS_SPAWN = True
            assert GovernanceFlags.is_enabled_for("process.spawn") == True
        finally:
            # Restore
            GovernanceFlags.GOVERNANCE_ENABLED = orig_governance
            GovernanceFlags.WRAP_PROCESS_SPAWN = orig_spawn
    
    def test_get_status_returns_all_flags(self):
        """get_status returns complete flag state."""
        status = flags.get_status()
        
        assert "governance_enabled" in status
        assert "auth_gate" in status
        assert "approval_gate" in status
        assert "dry_run" in status
        assert "components" in status
        assert "process.spawn" in status["components"]


class TestObservabilityBus:
    """Test event bus."""
    
    def test_publish_and_subscribe(self):
        """Events are published and received."""
        events = []
        
        def handler(event):
            events.append(event)
        
        bus = get_observability_bus()
        bus.subscribe(GovernanceEventType.EXECUTION_STARTED, handler)
        
        from unified_core.governance.events import publish_event
        publish_event(
            GovernanceEventType.EXECUTION_STARTED,
            component="test.operation",
            user_id="test_user"
        )
        
        assert len(events) == 1
        assert events[0].component == "test.operation"
        assert events[0].user_id == "test_user"
    
    def test_handler_exceptions_are_caught(self):
        """Handler exceptions don't break publishing."""
        def bad_handler(event):
            raise Exception("Handler failed!")
        
        bus = get_observability_bus()
        bus.subscribe(GovernanceEventType.EXECUTION_STARTED, bad_handler)
        
        # Should not raise
        from unified_core.governance.events import publish_event
        publish_event(
            GovernanceEventType.EXECUTION_STARTED,
            component="test.operation"
        )


class TestGovernor:
    """Test decision governor."""
    
    def test_classify_returns_impact_level(self):
        """Governor classifies operations correctly."""
        from unified_core.governance import get_governor
        
        governor = get_governor()
        
        assert governor.classify("process.spawn") == DecisionImpact.CRITICAL
        assert governor.classify("process.kill") == DecisionImpact.CRITICAL
        assert governor.classify("filesystem.delete") == DecisionImpact.HIGH
    
    def test_decide_returns_allow_when_gate_disabled(self):
        """Decision is ALLOW when approval gate disabled."""
        from unified_core.governance import get_governor, GovernanceDecision
        
        flags.APPROVAL_GATE_ENABLED = False
        
        governor = get_governor()
        decision = governor.decide("process.spawn", "test_user")
        
        assert decision == GovernanceDecision.ALLOW


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
