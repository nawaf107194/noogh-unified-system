"""
Test AMLA Fail-Closed Enforcement
Tests that actuators crash if AMLA enforcement is unavailable.
"""
import pytest
import sys
from unittest.mock import patch


def test_actuators_crash_without_amla():
    """
    CRITICAL SECURITY TEST:
    Verify that actuators refuse to load if AMLA enforcer is missing.
    
    This prevents the dangerous fail-open behavior where actuators
    would silently operate without governance.
    """
    # Simulate AMLA import failure
    with patch.dict(sys.modules, {'unified_core.core.amla_enforcer': None}):
        with pytest.raises(ImportError) as exc_info:
            # Force reload to trigger import
            if 'unified_core.core.actuators' in sys.modules:
                del sys.modules['unified_core.core.actuators']
            
            import unified_core.core.actuators
        
        
        # Verify error is about AMLA (message varies based on how import fails)
        error_msg = str(exc_info.value).lower()
        assert "amla" in error_msg or "enforcer" in error_msg, \
            f"Expected AMLA-related ImportError, got: {exc_info.value}"


def test_actuators_load_with_amla():
    """
    Verify that actuators load successfully when AMLA is available.
    """
    # This test ensures we didn't break normal operation
    try:
        from unified_core.core.actuators import FilesystemActuator
        from unified_core.core.amla_enforcer import AMLAEnforcedMixin
        
        # Verify FilesystemActuator inherits from AMLAEnforcedMixin
        assert issubclass(FilesystemActuator, AMLAEnforcedMixin)
        
    except ImportError as e:
        pytest.fail(f"Actuators should load when AMLA is available: {e}")


def test_amla_available_flag():
    """
    Verify AMLA_AVAILABLE flag is set correctly.
    """
    from unified_core.core.actuators import AMLA_AVAILABLE
    
    # Should always be True now (or module would have crashed)
    assert AMLA_AVAILABLE is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
