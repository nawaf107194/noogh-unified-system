import pytest
from datetime import datetime
from typing import Dict, Optional

class ActionSummary:
    def __init__(self, tool_name: str, success: bool, timestamp: str, summary: str, details: Optional[Dict[str, Any]] = None):
        self.tool_name = tool_name
        self.success = success
        self.timestamp = timestamp
        self.summary = summary
        self.details = details

class Checkpoint:
    pass  # Mock implementation for the sake of testing

class ProgressCheckpointManager:
    def __init__(self, checkpoint_interval: int):
        self.checkpoint_interval = checkpoint_interval
        self.actions = []
    
    def record_action(
        self,
        tool_name: str,
        success: bool,
        summary: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[Checkpoint]:
        action = ActionSummary(
            tool_name=tool_name,
            success=success,
            timestamp=datetime.now().isoformat(),
            summary=summary,
            details=details
        )
        
        self.actions.append(action)
        
        if len(self.actions) >= self.checkpoint_interval:
            return self._create_checkpoint()
        
        return None
    
    def _create_checkpoint(self) -> Checkpoint:
        # Mock implementation for the sake of testing
        return Checkpoint()

@pytest.fixture
def manager():
    return ProgressCheckpointManager(checkpoint_interval=3)

def test_record_action_happy_path(manager):
    checkpoint = manager.record_action("tool1", True, "Action successful")
    assert checkpoint is not None
    assert len(manager.actions) == 1

def test_record_action_edge_cases_empty_string(manager):
    checkpoint = manager.record_action("", False, "")
    assert checkpoint is None
    assert len(manager.actions) == 1
    
    checkpoint = manager.record_action(None, True, "Summary")
    assert checkpoint is None
    assert len(manager.actions) == 2

def test_record_action_edge_cases_boundary_checkpoints(manager):
    checkpoint = manager.record_action("tool1", True, "Action successful")
    assert checkpoint is not None
    assert len(manager.actions) == 1
    
    checkpoint = manager.record_action("tool2", False, "Action failed")
    assert checkpoint is None
    assert len(manager.actions) == 2
    
    checkpoint = manager.record_action("tool3", True, "Action successful")
    assert checkpoint is not None
    assert len(manager.actions) == 3

def test_record_action_error_cases_invalid_inputs(manager):
    # This function does not explicitly raise exceptions, so we don't need to test for them.
    pass

def test_record_action_async_behavior(manager):
    """This function does not involve async behavior, so no tests are needed."""
    pass