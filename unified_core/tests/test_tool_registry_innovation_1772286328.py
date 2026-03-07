import pytest
from unified_core.tool_registry import ToolRegistry

def test_get_processes_info_happy_path():
    registry = ToolRegistry()
    processes = registry._get_processes_info(limit=5)
    assert isinstance(processes, list)
    assert len(processes) == 5
    for process in processes:
        assert 'pid' in process
        assert 'name' in process
        assert 'memory_percent' in process

def test_get_processes_info_edge_case_empty():
    registry = ToolRegistry()
    processes = registry._get_processes_info(limit=0)
    assert isinstance(processes, list)
    assert len(processes) == 0

def test_get_processes_info_edge_case_none_limit():
    registry = ToolRegistry()
    processes = registry._get_processes_info()
    assert isinstance(processes, list)
    assert len(processes) <= 20

def test_get_processes_info_edge_case_boundary_limit():
    registry = ToolRegistry()
    processes = registry._get_processes_info(limit=100)
    assert isinstance(processes, list)
    assert len(processes) == min(100, psutil.Process().num_threads())

def test_get_processes_info_error_case_invalid_limit_type():
    registry = ToolRegistry()
    with pytest.raises(TypeError):
        processes = registry._get_processes_info(limit="invalid")

def test_get_processes_info_error_case_negative_limit():
    registry = ToolRegistry()
    processes = registry._get_processes_info(limit=-1)
    assert isinstance(processes, list)
    assert len(processes) == 0