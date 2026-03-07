import pytest
from app.core.validation import wrapper
from app.core.exceptions import ValidationError

def test_wrapper_happy_path():
    @wrapper(param_names=["x", "y"])
    def test_func(x, y):
        return x + y

    # Test with valid non-None values
    assert test_func(1, 2) == 3
    assert test_func("a", "b") == "ab"

def test_wrapper_edge_cases():
    @wrapper(param_names=["x"])
    def test_func(x):
        return x

    # Test with edge values that are not None
    assert test_func("") == ""
    assert test_func(0) == 0
    assert test_func(False) is False

def test_wrapper_error_cases():
    @wrapper(param_names=["x"])
    def test_func(x):
        return x

    # Test with None value
    with pytest.raises(ValidationError):
        test_func(None)

    # Test with missing parameter
    with pytest.raises(ValidationError):
        test_func()

def test_wrapper_async_function():
    @wrapper(param_names=["x"])
    async def test_func(x):
        return x

    # Test async function
    assert pytest.iscoroutinefunction(test_func)
    result = test_func(42)
    pytest.mark.asyncio
    async def inner_test():
        assert await result == 42
    inner_test()

def test_wrapper_no_parameters():
    @wrapper(param_names=[])
    def test_func():
        return "test"

    # Test function with no parameters
    assert test_func() == "test"

def test_wrapper_optional_parameters():
    @wrapper(param_names=["x"])
    def test_func(x, y=None):
        return x, y

    # Test with optional parameters
    assert test_func(1) == (1, None)
    assert test_func(1, 2) == (1, 2)