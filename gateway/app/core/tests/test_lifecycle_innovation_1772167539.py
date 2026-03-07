import pytest

from gateway.app.core.lifecycle import Lifecycle

def test_lifecycle_init_happy_path():
    lifecycle = Lifecycle()
    assert lifecycle.running is False
    assert lifecycle.task is None
    assert isinstance(lifecycle.hw, HardwareConsciousness)
    assert isinstance(lifecycle.brain, SelfGoverningAgent)
    assert isinstance(lifecycle.learner, CurriculumLearner)
    assert isinstance(lifecycle.senses, MetricsCollector)
    assert isinstance(lifecycle.reporter, Reporter)
    logger.info.assert_called_once_with("🟢 System Life Cycle initialized")

def test_lifecycle_init_edge_cases():
    # Assuming the functions get_hardware_consciousness(), etc., have edge cases
    with patch('gateway.app.core.lifecycle.get_hardware_consciousness', return_value=None):
        lifecycle = Lifecycle()
        assert lifecycle.hw is None

    with patch('gateway.app.core.lifecycle.get_self_governing_agent', return_value=None):
        lifecycle = Lifecycle()
        assert lifecycle.brain is None

    with patch('gateway.app.core.lifecycle.get_curriculum_learner', return_value=None):
        lifecycle = Lifecycle()
        assert lifecycle.learner is None

    with patch('gateway.app.core.lifecycle.get_metrics_collector', return_value=None):
        lifecycle = Lifecycle()
        assert lifecycle.senses is None

    with patch('gateway.app.core.lifecycle.get_reporter', return_value=None):
        lifecycle = Lifecycle()
        assert lifecycle.reporter is None

def test_lifecycle_init_async_behavior():
    # Assuming the functions are async and need to be awaited
    async def mock_get_hardware_consciousness():
        return HardwareConsciousness()

    with patch('gateway.app.core.lifecycle.get_hardware_consciousness', side_effect=mock_get_hardware_consciousness):
        lifecycle = Lifecycle()
        assert isinstance(lifecycle.hw, HardwareConsciousness)