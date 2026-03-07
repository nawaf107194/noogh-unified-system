import pytest
from typing import List
from neural_engine.progress_checkpoint_manager import Checkpoint, ProgressCheckpointManager

class MockCheckpoint(Checkpoint):
    def __init__(self, name: str):
        self.name = name

@pytest.fixture
def progress_checkpoint_manager():
    manager = ProgressCheckpointManager()
    manager.checkpoints = [MockCheckpoint(f"checkpoint_{i}") for i in range(5)]
    return manager

def test_get_all_checkpoints_happy_path(progress_checkpoint_manager):
    checkpoints = progress_checkpoint_manager.get_all_checkpoints()
    assert len(checkpoints) == 5
    for i, checkpoint in enumerate(checkpoints):
        assert checkpoint.name == f"checkpoint_{i}"

def test_get_all_checkpoints_empty(progress_checkpoint_manager):
    progress_checkpoint_manager.checkpoints = []
    checkpoints = progress_checkpoint_manager.get_all_checkpoints()
    assert len(checkpoints) == 0

def test_get_all_checkpoints_none():
    manager = ProgressCheckpointManager()
    manager.checkpoints = None
    with pytest.raises(AttributeError):
        manager.get_all_checkpoints()

def test_get_all_checkpoints_invalid_input(progress_checkpoint_manager):
    progress_checkpoint_manager.checkpoints = "not a list"
    with pytest.raises(AttributeError):
        progress_checkpoint_manager.get_all_checkpoints()

# Since the method is synchronous, there's no need to test async behavior.
# If the method were to become async in the future, you could use pytest-asyncio to write async tests.