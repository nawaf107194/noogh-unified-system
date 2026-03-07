import pytest

from src.shared.task_dependency_manager import TaskDependencyManager

def test_add_task_happy_path():
    manager = TaskDependencyManager()
    task_name = "task1"
    task_func = lambda: None
    depends_on = ["task2", "task3"]

    manager.add_task(task_name, task_func, depends_on)

    assert task_name in manager.tasks
    assert manager.tasks[task_name] == task_func
    assert task_name in manager.dependencies
    assert manager.dependencies[task_name] == depends_on

def test_add_task_no_dependencies():
    manager = TaskDependencyManager()
    task_name = "task1"
    task_func = lambda: None

    manager.add_task(task_name, task_func)

    assert task_name in manager.tasks
    assert manager.tasks[task_name] == task_func
    assert task_name in manager.dependencies
    assert manager.dependencies[task_name] == []

def test_add_task_empty_dependencies():
    manager = TaskDependencyManager()
    task_name = "task1"
    task_func = lambda: None
    depends_on = []

    manager.add_task(task_name, task_func, depends_on)

    assert task_name in manager.tasks
    assert manager.tasks[task_name] == task_func
    assert task_name in manager.dependencies
    assert manager.dependencies[task_name] == depends_on

def test_add_task_none_dependencies():
    manager = TaskDependencyManager()
    task_name = "task1"
    task_func = lambda: None
    depends_on = None

    manager.add_task(task_name, task_func, depends_on)

    assert task_name in manager.tasks
    assert manager.tasks[task_name] == task_func
    assert task_name in manager.dependencies
    assert manager.dependencies[task_name] == []

def test_add_task_invalid_task_name():
    with pytest.raises(TypeError):
        TaskDependencyManager().add_task(123, lambda: None)

def test_add_task_invalid_task_func():
    with pytest.raises(TypeError):
        TaskDependencyManager().add_task("task1", 123)