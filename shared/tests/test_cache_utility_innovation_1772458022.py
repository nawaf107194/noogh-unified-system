import pytest
import os
from noogh_unified_system.src.shared.cache_utility import CacheUtility

@pytest.fixture
def cache_utility():
    return CacheUtility(cache_dir="test_cache")

def test_happy_path(cache_utility, monkeypatch):
    def mock_func(*args, **kwargs):
        return "cached_result"
    
    with monkeypatch.context() as m:
        m.setattr('noogh_unified_system.src.shared.cache_utility.os.path.exists', lambda path: False)
        result = cache_utility.wrapper(mock_func)(1, 2, b=3)
        assert result == "cached_result"
        assert os.path.exists("test_cache/1_2_b=3.pkl")

def test_edge_case_empty_args(cache_utility, monkeypatch):
    def mock_func(*args, **kwargs):
        return "empty_args"
    
    with monkeypatch.context() as m:
        m.setattr('noogh_unified_system.src.shared.cache_utility.os.path.exists', lambda path: False)
        result = cache_utility.wrapper(mock_func)()
        assert result == "empty_args"
        assert os.path.exists("test_cache/_pkl")

def test_edge_case_none_args(cache_utility, monkeypatch):
    def mock_func(*args, **kwargs):
        return "none_args"
    
    with monkeypatch.context() as m:
        m.setattr('noogh_unified_system.src.shared.cache_utility.os.path.exists', lambda path: False)
        result = cache_utility.wrapper(mock_func)(None)
        assert result == "none_args"
        assert os.path.exists("test_cache/None_pkl")

def test_edge_case_boundary_int(cache_utility, monkeypatch):
    def mock_func(*args, **kwargs):
        return "boundary_int"
    
    with monkeypatch.context() as m:
        m.setattr('noogh_unified_system.src.shared.cache_utility.os.path.exists', lambda path: False)
        result = cache_utility.wrapper(mock_func)(2147483647)  # Max int
        assert result == "boundary_int"
        assert os.path.exists("test_cache/2147483647_pkl")

def test_edge_case_boundary_float(cache_utility, monkeypatch):
    def mock_func(*args, **kwargs):
        return "boundary_float"
    
    with monkeypatch.context() as m:
        m.setattr('noogh_unified_system.src.shared.cache_utility.os.path.exists', lambda path: False)
        result = cache_utility.wrapper(mock_func)(1.7976931348623157e+308)  # Max float
        assert result == "boundary_float"
        assert os.path.exists("test_cache/1_7976931348623157e+308_pkl")

def test_error_case_invalid_input(cache_utility, monkeypatch):
    def mock_func(*args, **kwargs):
        raise TypeError("Invalid input")
    
    with monkeypatch.context() as m:
        m.setattr('noogh_unified_system.src.shared.cache_utility.os.path.exists', lambda path: False)
        with pytest.raises(TypeError) as exc_info:
            cache_utility.wrapper(mock_func)("a", "b")
        assert str(exc_info.value) == "Invalid input"

def test_async_behavior(cache_utility, event_loop):
    async def mock_async_func(*args, **kwargs):
        return "async_result"
    
    result = event_loop.run_until_complete(cache_utility.wrapper(mock_async_func)(1, 2))
    assert result == "async_result"
    assert os.path.exists("test_cache/1_2.pkl")