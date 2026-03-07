import pytest

from shared.task_dependency_manager import TaskDependencyManager

def test_add_task_happy_path():
    manager = TaskDependencyManager()
    task_name = "task1"
    task_func = lambda: print("Task 1")
    depends_on = ["task2", "task3"]

    result = manager.add_task(task_name, task_func, depends_on)
    
    assert result is None
    assert manager.tasks[task_name] == task_func
    assert manager.dependencies[task_name] == depends_on

def test_add_task_no_dependencies():
    manager = TaskDependencyManager()
    task_name = "task1"
    task_func = lambda: print("Task 1")
    
    result = manager.add_task(task_name, task_func)
    
    assert result is None
    assert manager.tasks[task_name] == task_func
    assert manager.dependencies[task_name] == []

def test_add_task_empty_dependency_list():
    manager = TaskDependencyManager()
    task_name = "task1"
    task_func = lambda: print("Task 1")
    depends_on = []
    
    result = manager.add_task(task_name, task_func, depends_on)
    
    assert result is None
    assert manager.tasks[task_name] == task_func
    assert manager.dependencies[task_name] == []

def test_add_task_none_dependency_list():
    manager = TaskDependencyManager()
    task_name = "task1"
    task_func = lambda: print("Task 1")
    depends_on = None
    
    result = manager.add_task(task_name, task_func, depends_on)
    
    assert result is None
    assert manager.tasks[task_name] == task_func
    assert manager.dependencies[task_name] == []

def test_add_task_invalid_task_name():
    manager = TaskDependencyManager()
    task_name = 123  # Invalid input
    task_func = lambda: print("Task 1")
    
    result = manager.add_task(task_name, task_func)
    
    assert result is None
    assert not manager.tasks
    assert not manager.dependencies

def test_add_task_invalid_task_func():
    manager = TaskDependencyManager()
    task_name = "task1"
    task_func = 123  # Invalid input
    
    result = manager.add_task(task_name, task_func)
    
    assert result is None
    assert not manager.tasks
    assert not manager.dependencies

def test_add_task_duplicate_task_name():
    manager = TaskDependencyManager()
    task_name = "task1"
    task_func = lambda: print("Task 1")
    depends_on = ["task2", "task3"]
    
    # First add works
    result = manager.add_task(task_name, task_func, depends_on)
    assert result is None
    
    # Second add with same name should not change anything
    result = manager.add_task(task_name, lambda: print("Task 1"), ["task2"])
    assert result is None
    assert manager.tasks[task_name] == task_func
    assert manager.dependencies[task_name] == depends_on

def test_add_task_async_behavior():
    import asyncio
    
    async def async_task():
        await asyncio.sleep(0.1)
    
    manager = TaskDependencyManager()
    task_name = "async_task"
    task_func = async_task
    
    result = manager.add_task(task_name, task_func)
    
    assert result is None
    assert manager.tasks[task_name] == task_func
    assert manager.dependencies[task_name] == []