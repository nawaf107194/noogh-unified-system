import pytest
from unittest.mock import patch
from gateway.app.core.lifecycle import Lifecycle

@patch('gateway.app.core.lifecycle.get_hardware_consciousness')
@patch('gateway.app.core.lifecycle.get_self_governing_agent')
@patch('gateway.app.core.lifecycle.get_curriculum_learner')
@patch('gateway.app.core.lifecycle.get_metrics_collector')
@patch('gateway.app.core.lifecycle.get_reporter')
def test_init_happy_path(mock_get_reporter, mock_get_metrics_collector, mock_get_curriculum_learner, mock_get_self_governing_agent, mock_get_hardware_consciousness):
    lifecycle = Lifecycle()
    assert not lifecycle.running
    assert lifecycle.task is None
    assert isinstance(lifecycle.hw, type(mock_get_hardware_consciousness.return_value))
    assert isinstance(lifecycle.brain, type(mock_get_self_governing_agent.return_value))
    assert isinstance(lifecycle.learner, type(mock_get_curriculum_learner.return_value))
    assert isinstance(lifecycle.senses, type(mock_get_metrics_collector.return_value))
    assert isinstance(lifecycle.reporter, type(mock_get_reporter.return_value))
    mock_get_hardware_consciousness.assert_called_once()
    mock_get_self_governing_agent.assert_called_once()
    mock_get_curriculum_learner.assert_called_once()
    mock_get_metrics_collector.assert_called_once()
    mock_get_reporter.assert_called_once()

@patch('gateway.app.core.lifecycle.get_hardware_consciousness', return_value=None)
@patch('gateway.app.core.lifecycle.get_self_governing_agent')
@patch('gateway.app.core.lifecycle.get_curriculum_learner')
@patch('gateway.app.core.lifecycle.get_metrics_collector')
@patch('gateway.app.core.lifecycle.get_reporter')
def test_init_with_none_hardware_consciousness(mock_get_reporter, mock_get_metrics_collector, mock_get_curriculum_learner, mock_get_self_governing_agent, mock_get_hardware_consciousness):
    lifecycle = Lifecycle()
    assert not lifecycle.running
    assert lifecycle.task is None
    assert lifecycle.hw is None
    assert isinstance(lifecycle.brain, type(mock_get_self_governing_agent.return_value))
    assert isinstance(lifecycle.learner, type(mock_get_curriculum_learner.return_value))
    assert isinstance(lifecycle.senses, type(mock_get_metrics_collector.return_value))
    assert isinstance(lifecycle.reporter, type(mock_get_reporter.return_value))
    mock_get_hardware_consciousness.assert_called_once()
    mock_get_self_governing_agent.assert_called_once()
    mock_get_curriculum_learner.assert_called_once()
    mock_get_metrics_collector.assert_called_once()
    mock_get_reporter.assert_called_once()

@patch('gateway.app.core.lifecycle.get_hardware_consciousness', return_value='not an instance')
@patch('gateway.app.core.lifecycle.get_self_governing_agent')
@patch('gateway.app.core.lifecycle.get_curriculum_learner')
@patch('gateway.app.core.lifecycle.get_metrics_collector')
@patch('gateway.app.core.lifecycle.get_reporter')
def test_init_with_non_instance_hardware_consciousness(mock_get_reporter, mock_get_metrics_collector, mock_get_curriculum_learner, mock_get_self_governing_agent, mock_get_hardware_consciousness):
    lifecycle = Lifecycle()
    assert not lifecycle.running
    assert lifecycle.task is None
    assert isinstance(lifecycle.hw, str)
    assert lifecycle.hw == 'not an instance'
    assert isinstance(lifecycle.brain, type(mock_get_self_governing_agent.return_value))
    assert isinstance(lifecycle.learner, type(mock_get_curriculum_learner.return_value))
    assert isinstance(lifecycle.senses, type(mock_get_metrics_collector.return_value))
    assert isinstance(lifecycle.reporter, type(mock_get_reporter.return_value))
    mock_get_hardware_consciousness.assert_called_once()
    mock_get_self_governing_agent.assert_called_once()
    mock_get_curriculum_learner.assert_called_once()
    mock_get_metrics_collector.assert_called_once()
    mock_get_reporter.assert_called_once()

@patch('gateway.app.core.lifecycle.get_hardware_consciousness', side_effect=Exception)
def test_init_with_exception(mock_get_hardware_consciousness):
    with pytest.raises(Exception):
        Lifecycle()