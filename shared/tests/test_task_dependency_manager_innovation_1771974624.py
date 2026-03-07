import pytest

from shared.task_dependency_manager import TaskDependencyManager

def test_init_happy_path():
    manager = TaskDependencyManager()
    assert isinstance(manager.tasks, dict)
    assert isinstance(manager.dependencies, dict)

def test_init_empty_input():
    manager = TaskDependencyManager()
    assert manager.tasks == {}
    assert manager.dependencies == {}

def test_init_none_input():
    manager = TaskDependencyManager(None)
    assert manager.tasks == {}
    assert manager.dependencies == {}

def test_init_boundary_inputs():
    boundary_cases = [
        0,
        1,
        100,
        float('inf'),
        -1,
        -float('inf'),
        None,
        [],
        {},
        True,
        False,
        'some_string',
        b'binary_data',
    ]
    for case in boundary_cases:
        manager = TaskDependencyManager(case)
        assert manager.tasks == {}
        assert manager.dependencies == {}

def test_init_invalid_input():
    with pytest.raises(TypeError):
        TaskDependencyManager(123)  # Assuming the constructor does not accept integers