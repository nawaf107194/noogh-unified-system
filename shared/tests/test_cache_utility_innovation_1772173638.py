import pytest
import os
from shared.cache_utility import CacheUtility

def test_happy_path(tmpdir):
    cache_dir = str(tmpdir.mkdir('test_cache'))
    cache_util = CacheUtility(cache_dir)
    assert cache_util.cache_dir == cache_dir
    assert os.path.exists(cache_dir)

def test_edge_case_empty_string():
    with pytest.raises(ValueError) as e:
        CacheUtility('')
    assert "cache_dir cannot be empty" in str(e.value)

def test_edge_case_none():
    with pytest.raises(ValueError) as e:
        CacheUtility(None)
    assert "cache_dir cannot be None" in str(e.value)

def test_error_case_invalid_input():
    with pytest.raises(ValueError) as e:
        CacheUtility(123)
    assert "Invalid cache directory type. Expected a string." in str(e.value)

if __name__ == "__main__":
    pytest.main()