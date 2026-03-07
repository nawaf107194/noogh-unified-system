import pytest
from unittest.mock import patch, MagicMock
from unified_core.initialization import wait_for_startup, ComponentState

class MockUnifiedCore:
    REQUIRED_COMPONENTS = {'component1', 'component2'}
    _components = {'component1': ComponentState.READY, 'component2': ComponentState.READY}
    _startup_complete = False
    _failure_reason = None
    _lock = MagicMock()

def test_wait_for_startup_happy_path():
    with patch('time.sleep') as mock_sleep:
        wait_for_startup(MockUnifiedCore)
        assert MockUnifiedCore._startup_complete is True
        mock_sleep.assert_not_called()

def test_wait_for_startup_missing_component():
    MockUnifiedCore._components = {'component1': ComponentState.READY}
    with pytest.raises(RuntimeError) as exc_info:
        wait_for_startup(MockUnifiedCore)
    assert "Missing components: {'component2'}" in str(exc_info.value)

def test_wait_for_startup_failed_component():
    MockUnifiedCore._components = {'component1': ComponentState.FAILED, 'component2': ComponentState.READY}
    with pytest.raises(RuntimeError) as exc_info:
        wait_for_startup(MockUnifiedCore)
    assert "Failed components: ['component1']. Reason: None" in str(exc_info.value)

def test_wait_for_startup_not_ready_component():
    MockUnifiedCore._components = {'component1': ComponentState.NOT_READY, 'component2': ComponentState.READY}
    with pytest.raises(RuntimeError) as exc_info:
        wait_for_startup(MockUnifiedCore)
    assert "Startup timeout. Not ready: ['component1']" in str(exc_info.value)

def test_wait_for_startup_timeout():
    MockUnifiedCore.REQUIRED_COMPONENTS = {'component1'}
    MockUnifiedCore._components = {}
    with pytest.raises(RuntimeError) as exc_info:
        wait_for_startup(MockUnifiedCore, timeout=2.0)
    assert "Startup timeout. Missing components: {'component1'}" in str(exc_info.value)

def test_wait_for_startup_empty_required_components():
    MockUnifiedCore.REQUIRED_COMPONENTS = set()
    with patch('time.sleep') as mock_sleep:
        wait_for_startup(MockUnifiedCore)
        assert MockUnifiedCore._startup_complete is True
        mock_sleep.assert_not_called()

def test_wait_for_startup_none_timeout():
    with pytest.raises(TypeError) as exc_info:
        wait_for_startup(MockUnifiedCore, timeout=None)
    assert "None values are not allowed" in str(exc_info.value)

def test_wait_for_startup_negative_timeout():
    with pytest.raises(ValueError) as exc_info:
        wait_for_startup(MockUnifiedCore, timeout=-1.0)
    assert "Timeout must be a non-negative number" in str(exc_info.value)