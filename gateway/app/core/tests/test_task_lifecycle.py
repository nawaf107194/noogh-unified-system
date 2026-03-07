import pytest

from gateway.app.core.task_lifecycle import TaskLifecycle

def test_get_lifecycle_list_happy_path():
    task = TaskLifecycle()
    task.events = ["event1", "event2"]
    
    result = task.get_lifecycle_list()
    
    assert isinstance(result, list)
    assert len(result) == 2
    assert result == ["event1", "event2"]

def test_get_lifecycle_list_empty_list():
    task = TaskLifecycle()
    task.events = []
    
    result = task.get_lifecycle_list()
    
    assert isinstance(result, list)
    assert len(result) == 0

def test_get_lifecycle_list_none_events():
    task = TaskLifecycle()
    task.events = None
    
    result = task.get_lifecycle_list()
    
    assert isinstance(result, list)
    assert len(result) == 0

def test_get_lifecycle_list_boundary_condition():
    task = TaskLifecycle()
    task.events = ["event1"]
    
    result = task.get_lifecycle_list()
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result == ["event1"]

# Note: There are no error cases or async behavior in the provided function.
# Therefore, there is no need to test for specific exceptions or async behavior.