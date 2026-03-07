import pytest
from unittest.mock import MagicMock, patch

class MockMetaAgent:
    def __init__(self):
        self.actions = {}

    def register_action(self, action_name):
        self.actions[action_name] = action_name

@pytest.fixture
def dreamer():
    dreamer = Dreamer()
    dreamer._meta_agent = MockMetaAgent()
    return dreamer

@pytest.fixture
def mock_logger():
    with patch('path.to.your.module.logger') as mock_logger:
        yield mock_logger

@pytest.fixture
def mock_state():
    class MockState:
        def snapshot(self):
            return {
                'average_risk': 0.5,
                'success_rate': 0.9,
                'new_metric_1': 60.0,
                'new_metric_2': 40.0,
                'known_metric': 30.0
            }
    return MockState()

@pytest.fixture
def mock_history():
    return ['some', 'history', 'data']

def test_discover_new_goals_happy_path(dreamer, mock_state, mock_history, mock_logger):
    dreamer._discover_new_goals(mock_state, mock_history)
    assert 'SET_GOAL_OPTIMIZE_NEW_METRIC_1' in dreamer._meta_agent.actions
    mock_logger.warning.assert_called_once_with("Dreamer Discovery: Found high metric 'new_metric_1' (60.0). Inventing new goal type.")

def test_discover_new_goals_empty_state(dreamer, mock_history, mock_logger):
    empty_state = MagicMock(snapshot=lambda: {})
    dreamer._discover_new_goals(empty_state, mock_history)
    assert len(dreamer._meta_agent.actions) == 0
    mock_logger.warning.assert_not_called()

def test_discover_new_goals_none_state(dreamer, mock_history, mock_logger):
    dreamer._discover_new_goals(None, mock_history)
    assert len(dreamer._meta_agent.actions) == 0
    mock_logger.warning.assert_not_called()

def test_discover_new_goals_invalid_state(dreamer, mock_history, mock_logger):
    invalid_state = MagicMock(snapshot=MagicMock(side_effect=TypeError))
    dreamer._discover_new_goals(invalid_state, mock_history)
    assert len(dreamer._meta_agent.actions) == 0
    mock_logger.warning.assert_not_called()

def test_discover_new_goals_value_at_boundary(dreamer, mock_history, mock_logger):
    boundary_state = MagicMock(snapshot=lambda: {'boundary_metric': 50.0})
    dreamer._discover_new_goals(boundary_state, mock_history)
    assert len(dreamer._meta_agent.actions) == 0
    mock_logger.warning.assert_not_called()

def test_discover_new_goals_non_numeric_values(dreamer, mock_history, mock_logger):
    non_numeric_state = MagicMock(snapshot=lambda: {'non_numeric': 'text'})
    dreamer._discover_new_goals(non_numeric_state, mock_history)
    assert len(dreamer._meta_agent.actions) == 0
    mock_logger.warning.assert_not_called()

def test_discover_new_goals_existing_action(dreamer, mock_state, mock_history, mock_logger):
    existing_action = 'SET_GOAL_OPTIMIZE_KNOWN_METRIC'
    dreamer._meta_agent.actions[existing_action] = existing_action
    dreamer._discover_new_goals(mock_state, mock_history)
    assert len(dreamer._meta_agent.actions) == 2
    mock_logger.warning.assert_called_once_with("Dreamer Discovery: Found high metric 'new_metric_1' (60.0). Inventing new goal type.")