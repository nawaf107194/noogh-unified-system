import pytest

from unified_core.db.lru_cache import wrapper

def test_wrapper_happy_path():
    def sample_func(x):
        return x * 2
    
    wrapped_func = wrapper(sample_func)
    assert wrapped_func(5) == 10

def test_wrapper_edge_case_empty_args():
    def sample_func():
        return "Hello"
    
    wrapped_func = wrapper(sample_func)
    assert wrapped_func() == "Hello"

def test_wrapper_edge_case_none_arg():
    def sample_func(x):
        return x is None
    
    wrapped_func = wrapper(sample_func)
    assert wrapped_func(None) is True

def test_wrapper_error_case_invalid_input():
    def sample_func(x):
        if not isinstance(x, int):
            raise ValueError("Input must be an integer")
        return x * 2
    
    wrapped_func = wrapper(sample_func)
    
    with pytest.raises(ValueError) as exc_info:
        wrapped_func("a")

    assert str(exc_info.value) == "Input must be an integer"

def test_wrapper_async_behavior():
    import asyncio

    async def sample_async_func(x):
        await asyncio.sleep(0.1)
        return x * 2
    
    wrapped_func = wrapper(sample_async_func)
    
    result = asyncio.run(wrapped_func(5))
    assert result == 10