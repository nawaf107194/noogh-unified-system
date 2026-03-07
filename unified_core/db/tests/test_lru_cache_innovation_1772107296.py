import pytest
from functools import lru_cache
from typing import Callable

class LRUCacheDecorator:
    def __init__(self, maxsize: int):
        self.maxsize = maxsize
    
    def __call__(self, func: Callable) -> Callable:
        @lru_cache(maxsize=self.maxsize)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

def example_function(x):
    return x * 2

def test_lru_cache_decorator_happy_path():
    decorator = LRUCacheDecorator(3)
    cached_func = decorator(example_function)
    
    assert cached_func(1) == 2
    assert cached_func(1) == 2  # Should retrieve from cache
    
    assert cached_func(2) == 4
    assert cached_func(2) == 4  # Should retrieve from cache

def test_lru_cache_decorator_edge_cases():
    decorator = LRUCacheDecorator(3)
    
    # Test with empty input
    def empty_input_func():
        return None
    
    cached_empty_func = decorator(empty_input_func)
    
    assert cached_empty_func() is None
    assert cached_empty_func() is None  # Should retrieve from cache
    
    # Test with boundary values
    def boundary_func(x):
        if x == 0:
            return 'zero'
        elif x == 1:
            return 'one'
    
    cached_boundary_func = decorator(boundary_func)
    
    assert cached_boundary_func(0) == 'zero'
    assert cached_boundary_func(0) == 'zero'  # Should retrieve from cache
    assert cached_boundary_func(1) == 'one'
    assert cached_boundary_func(1) == 'one'  # Should retrieve from cache

def test_lru_cache_decorator_error_cases():
    decorator = LRUCacheDecorator(-1)
    
    with pytest.raises(ValueError):
        decorator(example_function)

def test_lru_cache_decorator_async_behavior():
    import asyncio
    
    async def async_example_function(x):
        await asyncio.sleep(0.1)  # Simulate an I/O operation
        return x * 2
    
    decorator = LRUCacheDecorator(3)
    
    cached_async_func = decorator(async_example_function)
    
    result = asyncio.run(cached_async_func(1))
    assert result == 2
    
    result = asyncio.run(cached_async_func(1))
    assert result == 2  # Should retrieve from cache