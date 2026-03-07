import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock

# Assuming the class containing the record_action method is named ProgressCheckpointManager
class ProgressCheckpointManager:
    def __init__(self):
        self.actions = []
        self.checkpoint_interval = 5  # Example interval value

    def _create_checkpoint(self):
        # This is a mock implementation of the _create_checkpoint method
        return Checkpoint(self.actions[-self.checkpoint_interval:])

class Checkpoint:
    def __init__(self, actions):
        self.actions = actions

class ActionSummary:
    def __init__(self, tool_name: str, success: bool, timestamp: str, summary: str, details: Dict[str, Any]):
        self.tool_name = tool_name
        self.success = success
        self.timestamp = timestamp
        self.summary = summary
        self.details = details

@pytest.fixture
def manager():
    return ProgressCheckpointManager()

def test_record_action_happy_path(manager):
    tool_name = "test_tool"
    success = True
    summary = "Action was successful"
    details = {"key": "value"}
    
    result = manager.record_action(tool_name, success, summary, details)
    assert len(manager.actions) == 1
    assert result is None  # Since the number of actions is less than the checkpoint interval
    
def test_record_action_edge_cases(manager):
    # Test with empty strings and None values
    tool_name = ""
    success = False
    summary = ""
    details = None
    
    result = manager.record_action(tool_name, success, summary, details)
    assert len(manager.actions) == 1
    assert result is None
    
def test_record_action_error_cases(manager):
    # Test with invalid types
    with pytest.raises(TypeError):
        manager.record_action(123, True, "Summary", {"key": "value"})
    with pytest.raises(TypeError):
        manager.record_action("Tool", "True", "Summary", {"key": "value"})

def test_record_action_create_checkpoint(manager):
    # Add actions until the checkpoint interval is reached
    for i in range(manager.checkpoint_interval):
        result = manager.record_action(f"tool_{i}", True, f"Action {i} successful", {"key": "value"})
        if i < manager.checkpoint_interval - 1:
            assert result is None
        else:
            assert isinstance(result, Checkpoint)
            assert len(result.actions) == manager.checkpoint_interval

def test_record_action_async_behavior(manager):
    # Assuming there's an async version of record_action, here's how you might test it.
    # For now, we're just mocking it as a synchronous call.
    mock_record_action = Mock(wraps=manager.record_action)
    manager.record_action = mock_record_action
    
    tool_name = "async_tool"
    success = True
    summary = "Async action was successful"
    details = {"key": "value"}
    
    result = manager.record_action(tool_name, success, summary, details)
    mock_record_action.assert_called_once_with(tool_name, success, summary, details)
    assert len(manager.actions) == 1
    assert result is None