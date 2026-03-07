import pytest

from shared.task_dependency_manager import TaskDependencyManager


@pytest.fixture
def task_manager():
    return TaskDependencyManager()


def test_add_task_happy_path(task_manager):
    task_name = "test_task"
    task_func = lambda: None
    depends_on = ["dependency1", "dependency2"]

    result = task_manager.add_task(task_name, task_func, depends_on)

    assert result is None
    assert task_name in task_manager.tasks
    assert task_manager.tasks[task_name] == task_func
    assert task_name in task_manager.dependencies
    assert task_manager.dependencies[task_name] == depends_on


def test_add_task_empty_dependency_list(task_manager):
    task_name = "test_task"
    task_func = lambda: None
    depends_on = []

    result = task_manager.add_task(task_name, task_func, depends_on)

    assert result is None
    assert task_name in task_manager.tasks
    assert task_manager.tasks[task_name] == task_func
    assert task_name in task_manager.dependencies
    assert task_manager.dependencies[task_name] == depends_on


def test_add_task_none_dependency(task_manager):
    task_name = "test_task"
    task_func = lambda: None

    result = task_manager.add_task(task_name, task_func)

    assert result is None
    assert task_name in task_manager.tasks
    assert task_manager.tasks[task_name] == task_func
    assert task_name in task_manager.dependencies
    assert task_manager.dependencies[task_name] == []


def test_add_task_invalid_task_name_type(task_manager):
    invalid_task_name = 12345
    task_func = lambda: None

    with pytest.raises(TypeError) as exc_info:
        task_manager.add_task(invalid_task_name, task_func)

    assert "task_name must be a string" in str(exc_info.value)


def test_add_task_invalid_task_func_type(task_manager):
    task_name = "test_task"
    invalid_task_func = 12345

    with pytest.raises(TypeError) as exc_info:
        task_manager.add_task(task_name, invalid_task_func)

    assert "task_func must be a callable" in str(exc_info.value)


def test_add_task_duplicate_task(task_manager):
    task_name = "test_task"
    task_func = lambda: None
    depends_on = ["dependency1", "dependency2"]

    result = task_manager.add_task(task_name, task_func, depends_on)
    assert result is None

    with pytest.raises(ValueError) as exc_info:
        task_manager.add_task(task_name, task_func, depends_on)

    assert "Task already exists" in str(exc_info.value)