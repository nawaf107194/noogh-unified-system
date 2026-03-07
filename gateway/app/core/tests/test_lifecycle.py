import pytest
from unittest.mock import patch, MagicMock
from gateway.app.core.lifecycle import Lifecycle, get_hardware_consciousness, get_self_governing_agent, get_curriculum_learner, get_metrics_collector, get_reporter

@pytest.fixture
def lifecycle_instance():
    return Lifecycle()

def test_init_happy_path(lifecycle_instance):
    assert lifecycle_instance.running is False
    assert lifecycle_instance.task is None
    assert isinstance(lifecycle_instance.hw, MagicMock)
    assert isinstance(lifecycle_instance.brain, MagicMock)
    assert isinstance(lifecycle_instance.learner, MagicMock)
    assert isinstance(lifecycle_instance.senses, MagicMock)
    assert isinstance(lifecycle_instance.reporter, MagicMock)

@patch('gateway.app.core.lifecycle.get_hardware_consciousness', return_value=None)
@patch('gateway.app.core.lifecycle.get_self_governing_agent', return_value=None)
@patch('gateway.app.core.lifecycle.get_curriculum_learner', return_value=None)
@patch('gateway.app.core.lifecycle.get_metrics_collector', return_value=None)
@patch('gateway.app.core.lifecycle.get_reporter', return_value=None)
def test_init_edge_cases(get_reporter_mock, get_metrics_collector_mock, get_curriculum_learner_mock, get_self_governing_agent_mock, get_hardware_consciousness_mock):
    lifecycle = Lifecycle()
    assert lifecycle.hw is None
    assert lifecycle.brain is None
    assert lifecycle.learner is None
    assert lifecycle.senses is None
    assert lifecycle.reporter is None

@patch('gateway.app.core.lifecycle.get_hardware_consciousness', side_effect=Exception("Failed to initialize hardware"))
@patch('gateway.app.core.lifecycle.get_self_governing_agent', side_effect=Exception("Failed to initialize brain"))
@patch('gateway.app.core.lifecycle.get_curriculum_learner', side_effect=Exception("Failed to initialize learner"))
@patch('gateway.app.core.lifecycle.get_metrics_collector', side_effect=Exception("Failed to initialize senses"))
@patch('gateway.app.core.lifecycle.get_reporter', side_effect=Exception("Failed to initialize reporter"))
def test_init_error_cases(get_reporter_mock, get_metrics_collector_mock, get_curriculum_learner_mock, get_self_governing_agent_mock, get_hardware_consciousness_mock):
    with pytest.raises(Exception) as excinfo:
        Lifecycle()
    assert "Failed to initialize hardware" in str(excinfo.value)

@pytest.mark.asyncio
async def test_async_behavior(lifecycle_instance):
    # Since there's no actual async behavior in the init method, this test is more of a placeholder.
    # If there were an async task being set up, we would mock it and check if it was properly assigned.
    assert lifecycle_instance.task is None