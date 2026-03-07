import pytest
from typing import Callable, List

class TaskDependencyManager:
    def __init__(self):
        self.tasks = {}
        self.dependencies = {}

    def add_task(self, task_name: str, task_func: Callable, depends_on: List[str] = None):
        """Add a new task with its dependencies."""
        self.tasks[task_name] = task_func
        self.dependencies[task_name] = depends_on if depends_on else []

def test_add_task_happy_path():
    manager = TaskDependencyManager()
    def sample_task():
        return "Task Executed"
    
    manager.add_task("sample_task", sample_task, ["dependency1", "dependency2"])
    assert manager.tasks == {"sample_task": sample_task}
    assert manager.dependencies == {"sample_task": ["dependency1", "dependency2"]}

def test_add_task_no_dependencies():
    manager = TaskDependencyManager()
    def sample_task():
        return "Task Executed"
    
    manager.add_task("sample_task", sample_task)
    assert manager.tasks == {"sample_task": sample_task}
    assert manager.dependencies == {"sample_task": []}

def test_add_task_with_empty_dependency_list():
    manager = TaskDependencyManager()
    def sample_task():
        return "Task Executed"
    
    manager.add_task("sample_task", sample_task, [])
    assert manager.tasks == {"sample_task": sample_task}
    assert manager.dependencies == {"sample_task": []}

def test_add_task_with_none_dependencies():
    manager = TaskDependencyManager()
    def sample_task():
        return "Task Executed"
    
    manager.add_task("sample_task", sample_task, None)
    assert manager.tasks == {"sample_task": sample_task}
    assert manager.dependencies == {"sample_task": []}

def test_add_task_with_invalid_task_name():
    manager = TaskDependencyManager()
    def sample_task():
        return "Task Executed"
    
    with pytest.raises(ValueError):
        manager.add_task(None, sample_task)

def test_add_task_with_invalid_task_func():
    manager = TaskDependencyManager()
    depends_on = ["dependency1", "dependency2"]
    
    with pytest.raises(TypeError):
        manager.add_task("sample_task", None, depends_on)