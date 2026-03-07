import pytest

from neural_engine.progress_checkpoint_manager import get_checkpoint_manager, ProgressCheckpointManager

@pytest.fixture(autouse=True)
def reset_global_checkpoint_manager():
    global _global_checkpoint_manager
    _global_checkpoint_manager = None

def test_get_checkpoint_manager_happy_path():
    manager = get_checkpoint_manager(interval=4)
    assert isinstance(manager, ProgressCheckpointManager)
    assert manager.interval == 4

def test_get_checkpoint_manager_edge_case_interval_zero():
    manager1 = get_checkpoint_manager(interval=0)
    manager2 = get_checkpoint_manager(interval=0)
    assert _global_checkpoint_manager is not None
    assert manager1 is manager2
    assert manager1.interval == 0

def test_get_checkpoint_manager_edge_case_interval_negative():
    manager1 = get_checkpoint_manager(interval=-5)
    manager2 = get_checkpoint_manager(interval=-5)
    assert _global_checkpoint_manager is not None
    assert manager1 is manager2
    assert manager1.interval == -5

def test_get_checkpoint_manager_edge_case_interval_none():
    with pytest.raises(TypeError) as exc_info:
        get_checkpoint_manager(None)
    assert str(exc_info.value) == "Interval must be an integer, got <class 'NoneType'>"

def test_get_checkpoint_manager_error_non_integer():
    with pytest.raises(TypeError) as exc_info:
        get_checkpoint_manager("4")
    assert str(exc_info.value) == "Interval must be an integer, got <class 'str'>"