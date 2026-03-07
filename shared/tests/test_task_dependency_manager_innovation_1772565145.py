import pytest

def test_task_dependency_manager_init_happy_path():
    """Test normal initialization of TaskDependencyManager"""
    manager = TaskDependencyManager()
    assert manager.tasks == {}
    assert manager.dependencies == {}
    assert isinstance(manager.tasks, dict)
    assert isinstance(manager.dependencies, dict)

def test_task_dependency_manager_init_edge_cases():
    """Test edge cases for TaskDependencyManager initialization"""
    # Test default initialization
    manager = TaskDependencyManager()
    assert manager.tasks == {}
    assert manager.dependencies == {}
    
    # Test type assertions
    assert isinstance(manager.tasks, dict)
    assert isinstance(manager.dependencies, dict)