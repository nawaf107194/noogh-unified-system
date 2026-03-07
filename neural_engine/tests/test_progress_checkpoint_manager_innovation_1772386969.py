import pytest

class MockCheckpoint:
    def __init__(self, actions_count=0, actions=None):
        self.actions_count = actions_count
        self.actions = actions if actions is not None else []

class MockAction:
    def __init__(self, success=True):
        self.success = success

def test_get_overall_stats_happy_path():
    manager = ProgressCheckpointManager()
    manager.checkpoints = [
        MockCheckpoint(2, [MockAction(True), MockAction(False)]),
        MockCheckpoint(3, [MockAction(True), MockAction(True), MockAction(True)])
    ]
    manager.actions = [MockAction(True), MockAction(True)]

    stats = manager.get_overall_stats()

    assert stats == {
        "total_checkpoints": 2,
        "total_actions": 8,
        "successful_actions": 6,
        "success_rate": 75.0,
        "pending_actions": 2
    }

def test_get_overall_stats_empty_checkpoints():
    manager = ProgressCheckpointManager()
    manager.checkpoints = []
    manager.actions = [MockAction(True), MockAction(False)]

    stats = manager.get_overall_stats()

    assert stats == {
        "total_checkpoints": 0,
        "total_actions": 2,
        "successful_actions": 1,
        "success_rate": 50.0,
        "pending_actions": 2
    }

def test_get_overall_stats_no_actions():
    manager = ProgressCheckpointManager()
    manager.checkpoints = [
        MockCheckpoint(2, [MockAction(True), MockAction(False)]),
        MockCheckpoint(3, [MockAction(True), MockAction(True), MockAction(True)])
    ]
    manager.actions = []

    stats = manager.get_overall_stats()

    assert stats == {
        "total_checkpoints": 2,
        "total_actions": 5,
        "successful_actions": 3,
        "success_rate": 60.0,
        "pending_actions": 0
    }

def test_get_overall_stats_no_successful_actions():
    manager = ProgressCheckpointManager()
    manager.checkpoints = [
        MockCheckpoint(2, [MockAction(False), MockAction(False)]),
        MockCheckpoint(3, [MockAction(False), MockAction(False), MockAction(False)])
    ]
    manager.actions = []

    stats = manager.get_overall_stats()

    assert stats == {
        "total_checkpoints": 2,
        "total_actions": 5,
        "successful_actions": 0,
        "success_rate": 0.0,
        "pending_actions": 0
    }

def test_get_overall_stats_all_successful_actions():
    manager = ProgressCheckpointManager()
    manager.checkpoints = [
        MockCheckpoint(2, [MockAction(True), MockAction(True)]),
        MockCheckpoint(3, [MockAction(True), MockAction(True), MockAction(True)])
    ]
    manager.actions = []

    stats = manager.get_overall_stats()

    assert stats == {
        "total_checkpoints": 2,
        "total_actions": 5,
        "successful_actions": 5,
        "success_rate": 100.0,
        "pending_actions": 0
    }

def test_get_overall_stats_no_checkpoints():
    manager = ProgressCheckpointManager()
    manager.checkpoints = []
    manager.actions = []

    stats = manager.get_overall_stats()

    assert stats == {
        "total_checkpoints": 0,
        "total_actions": 0,
        "successful_actions": 0,
        "success_rate": 0.0,
        "pending_actions": 0
    }