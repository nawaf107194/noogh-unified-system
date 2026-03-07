import pytest

from gateway.app.core.task_lifecycle import TaskState, transition

class MockTaskLifecycle:
    def __init__(self):
        self.state = None
        self.events = []
        self._save_metadata = lambda: None

def test_transition_happy_path():
    task_lifecycle = MockTaskLifecycle()
    new_state = TaskState.IN_PROGRESS
    info = "Task started"

    transition(task_lifecycle, new_state, info)

    assert task_lifecycle.state == new_state
    assert task_lifecycle.events == [f"{new_state.value}: {info}"]

def test_transition_no_info():
    task_lifecycle = MockTaskLifecycle()
    new_state = TaskState.COMPLETED

    transition(task_lifecycle, new_state)

    assert task_lifecycle.state == new_state
    assert task_lifecycle.events == [f"{new_state.value}"]


def test_transition_none_info():
    task_lifecycle = MockTaskLifecycle()
    new_state = TaskState.PAUSED
    info = None

    transition(task_lifecycle, new_state, info)

    assert task_lifecycle.state == new_state
    assert task_lifecycle.events == [f"{new_state.value}"]

def test_transition_invalid_state():
    task_lifecycle = MockTaskLifecycle()
    new_state = "INVALID_STATE"
    info = "Invalid state"

    transition(task_lifecycle, new_state, info)

    assert task_lifecycle.state is None
    assert task_lifecycle.events == [f"INVALID_STATE: {info}"]