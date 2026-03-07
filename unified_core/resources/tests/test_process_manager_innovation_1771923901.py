import pytest
from datetime import datetime, timedelta
import psutil

from unified_core.resources.process_manager import ProcessManager, ManagedProcess

class MockProcessManager(ProcessManager):
    def __init__(self):
        self._priority_overrides = {}
    
    def _infer_priority(self, name, pid):
        return 0

@pytest.fixture
def mock_pm():
    return MockProcessManager()

def test_get_all_processes_happy_path(mock_pm):
    # Simulate psutil.process_iter returning some processes
    processes_info = [
        {'pid': 1, 'name': 'process1', 'username': 'user1', 'cpu_percent': 0.5, 'memory_info': {'rss': 1024 * 1024}, 'create_time': datetime.now().timestamp()},
        {'pid': 2, 'name': 'process2', 'username': 'user2', 'cpu_percent': 0.3, 'memory_info': {'rss': 512 * 1024}, 'create_time': (datetime.now() - timedelta(seconds=1)).timestamp()}
    ]
    
    mock_pm._priority_overrides = {1: 1}
    
    with pytest.mock.patch('psutil.process_iter', return_value=[psutil.Process(pid=d['pid'], info=d) for d in processes_info]):
        result = mock_pm.get_all_processes()
        
        assert len(result) == 2
        assert all(isinstance(process, ManagedProcess) for process in result)
        assert result[0].pid == 1
        assert result[0].name == 'process1'
        assert result[0].priority == 1
        assert result[0].cpu_percent == 0.5
        assert result[0].memory_mb == 1.0
        assert result[0].gpu_memory_mb == 0.0
        assert result[1].pid == 2
        assert result[1].name == 'process2'
        assert result[1].priority == 0
        assert result[1].cpu_percent == 0.3
        assert result[1].memory_mb == 0.5
        assert result[1].gpu_memory_mb == 0.0

def test_get_all_processes_empty(mock_pm):
    with pytest.mock.patch('psutil.process_iter', return_value=[]):
        result = mock_pm.get_all_processes()
        
        assert len(result) == 0

def test_get_all_processes_error_cases(mock_pm):
    # Simulate psutil.process_iter raising an AccessDenied exception
    with pytest.mock.patch('psutil.process_iter', side_effect=psutil.AccessDenied):
        result = mock_pm.get_all_processes()
        
        assert result is None

def test_get_all_processes_invalid_sort_key(mock_pm):
    # Simulate an invalid sort key
    with pytest.raises(KeyError):
        mock_pm.get_all_processes(sort_by="invalid")

def test_get_all_processes_async_behavior(mock_pm):
    # This function does not have any async behavior, so this test is a placeholder
    pass