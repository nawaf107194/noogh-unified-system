import pytest

class TaskDependencyManager:
    def __init__(self):
        self.tasks = {}
        self.dependencies = {}

    def add_task(self, task_name: str, task_func: Callable, depends_on: List[str] = None):
        """Add a new task with its dependencies."""
        self.tasks[task_name] = task_func
        self.dependencies[task_name] = depends_on if depends_on else []

@pytest.fixture
def manager():
    return TaskDependencyManager()

def test_happy_path(manager):
    # Normal inputs
    def dummy_task():
        pass
    
    manager.add_task('dummy_task', dummy_task, ['pre_task'])
    assert 'dummy_task' in manager.tasks
    assert 'dummy_task' in manager.dependencies
    assert manager.dependencies['dummy_task'] == ['pre_task']

def test_empty_dependencies(manager):
    # Empty dependencies list
    def empty_task():
        pass
    
    manager.add_task('empty_task', empty_task, [])
    assert manager.dependencies['empty_task'] == []

def test_none_dependencies(manager):
    # Dependencies as None
    def none_task():
        pass
    
    manager.add_task('none_task', none_task, None)
    assert manager.dependencies['none_task'] == []

def test_no_dependencies(manager):
    # No dependencies provided
    def no_deps_task():
        pass
    
    manager.add_task('no_deps_task', no_deps_task)
    assert manager.dependencies['no_deps_task'] == []

def test_invalid_task_name(manager):
    # Invalid task name (not a string)
    def invalid_name_task():
        pass
    
    with pytest.raises(TypeError):
        manager.add_task(123, invalid_name_task, ['pre_task'])

def test_invalid_task_function(manager):
    # Invalid task function (not callable)
    with pytest.raises(TypeError):
        manager.add_task('invalid_func_task', 123, ['pre_task'])

def test_invalid_dependencies_list(manager):
    # Invalid dependencies list (not a list)
    def invalid_deps_task():
        pass
    
    with pytest.raises(TypeError):
        manager.add_task('invalid_deps_task', invalid_deps_task, 'pre_task')

def test_async_behavior(manager):
    # Test with an async function
    async def async_task():
        await asyncio.sleep(0.1)
    
    manager.add_task('async_task', async_task, ['pre_task'])
    assert 'async_task' in manager.tasks
    assert 'async_task' in manager.dependencies
    assert manager.dependencies['async_task'] == ['pre_task']