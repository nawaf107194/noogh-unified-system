import pytest
from unittest.mock import patch, MagicMock
from unified_core.resources.process_manager import ProcessManager, ManagedProcess, ProcessPriority
import psutil

@pytest.fixture
def process_manager():
    return ProcessManager()

@patch('psutil.Process')
def test_register_process_happy_path(mock_psutil_Process, process_manager):
    pid = 12345
    owner = "user1"
    mock_proc = MagicMock()
    mock_proc.name.return_value = "test_process"
    mock_proc.cpu_percent.return_value = 5.0
    mock_proc.memory_info.return_value.rss = 1048576  # 1MB
    mock_psutil_Process.return_value = mock_proc
    
    process_manager.register_process(pid, owner)
    
    assert pid in process_manager._managed_processes
    managed_process = process_manager._managed_processes[pid]
    assert managed_process.pid == pid
    assert managed_process.name == "test_process"
    assert managed_process.priority == ProcessPriority.NORMAL
    assert managed_process.cpu_percent == 5.0
    assert managed_process.memory_mb == 1.0
    assert managed_process.owner == owner
    assert isinstance(managed_process.started_at, datetime)

@patch('psutil.Process')
def test_register_process_edge_cases(mock_psutil_Process, process_manager):
    pid = None
    owner = ""
    
    with pytest.raises(ValueError) as exc_info:
        process_manager.register_process(pid, owner)
    assert "pid cannot be None" in str(exc_info.value)
    
    pid = 12345
    mock_psutil_Process.side_effect = psutil.NoSuchProcess
    
    process_manager.register_process(pid, owner)
    assert pid not in process_manager._managed_processes

@patch('psutil.Process')
def test_register_process_error_cases(mock_psutil_Process, process_manager):
    pid = 12345
    owner = "user1"
    
    mock_proc = MagicMock()
    mock_proc.cpu_percent.side_effect = psutil.AccessDenied
    
    with pytest.raises(psutil.AccessDenied) as exc_info:
        process_manager.register_process(pid, owner)
    assert "Access denied" in str(exc_info.value)

@patch('unified_core.resources.process_manager.ProcessManager.register_process')
def test_register_process_async_behavior(mock_register_process, process_manager):
    pid = 12345
    owner = "user1"
    
    async def simulate_register():
        await process_manager.register_process(pid, owner)
    
    pytest.assume(asyncio.run(simulate_register()))
    mock_register_process.assert_awaited_once_with(pid, owner)