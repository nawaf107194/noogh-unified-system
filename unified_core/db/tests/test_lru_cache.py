import pytest

from unified_core.db.lru_cache import LRUCache

class TestLRUCacheInit:

    @pytest.mark.parametrize("maxsize", [
        10,  # Happy path with a positive integer
        0,   # Boundary case with zero (should still work)
        -5,  # Edge case: negative integer (expected to raise ValueError if explicitly raised)
        None # Edge case: None should be handled gracefully without raising an exception
    ])
    def test_init_happy_path(self, maxsize):
        cache = LRUCache(maxsize=maxsize)
        assert isinstance(cache.cache, dict)
        assert cache.maxsize == maxsize

    def test_init_error_case_negative_maxsize(self):
        with pytest.raises(ValueError) as exc_info:
            cache = LRUCache(maxsize=-5)
        assert str(exc_info.value) == "maxsize must be a non-negative integer"

    def test_init_edge_case_none_maxsize(self):
        cache = LRUCache(maxsize=None)
        assert isinstance(cache.cache, dict)
        assert cache.maxsize is None

    def test_init_no_args(self):
        with pytest.raises(TypeError) as exc_info:
            cache = LRUCache()
        assert str(exc_info.value) == "__init__() missing 1 required positional argument: 'maxsize'"