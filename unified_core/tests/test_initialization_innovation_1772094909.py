import pytest
from unittest.mock import patch, Mock
import time

from unified_core.initialization import wait_for_startup

@pytest.fixture
def mock_components():
    with patch('unified_core.initialization.ComponentState') as mock_state:
        component_state = {
            'component1': mock_state.READY,
            'component2': mock_state.FAILED,
            'component3': mock_state.NOT_READY
        }
        cls = Mock(_lock=Mock(), _components=component_state, REQUIRED_COMPONENTS=component_state.keys())
        yield cls

def test_wait_for_startup_happy_path(mock_components):
    with patch('unified_core.initialization.time.sleep') as mock_sleep:
        wait_for_startup.__self__ = mock_components
        with pytest.raises(RuntimeError) as exc_info:
            wait_for_startup()
        assert "Startup failed. Failed components: {'component2'}. Reason:" in str(exc_info.value)

def test_wait_for_startup_no_missing_components(mock_components):
    mock_components._components = {name: ComponentState.READY for name in mock_components.REQUIRED_COMPONENTS}
    with patch('unified_core.initialization.time.sleep') as mock_sleep:
        wait_for_startup.__self__ = mock_components
        wait_for_startup()
        assert mock_components._startup_complete is True

def test_wait_for_startup_timeout(mock_components):
    mock_components._components = {name: ComponentState.NOT_READY for name in mock_components.REQUIRED_COMPONENTS}
    with patch('unified_core.initialization.time.sleep') as mock_sleep:
        mock_time = Mock(side_effect=[0, 15, 30])
        with patch('unified_core.initialization.time.time', mock_time):
            with pytest.raises(RuntimeError) as exc_info:
                wait_for_startup()
            assert "Startup timeout. Not ready: {'component1', 'component2', 'component3'}" in str(exc_info.value)

def test_wait_for_startup_invalid_input():
    with pytest.raises(TypeError):
        wait_for_startup(0)