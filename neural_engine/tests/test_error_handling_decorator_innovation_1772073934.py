import pytest
import logging

def wrapper(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the exception
            logging.error(f"Error occurred in {func.__name__}: {str(e)}")
            # Optionally re-raise the exception if needed
            raise

    return inner

# Mock function to test wrapper behavior
def mock_func():
    return 42

@pytest.fixture
def wrapped_func():
    return wrapper(mock_func)

def test_happy_path(wrapped_func):
    assert wrapped_func() == 42

def test_edge_case_none(wrapped_func):
    def edge_func():
        return None
    
    wrapped_edge_func = wrapper(edge_func)
    assert wrapped_edge_func() is None

async def async_mock_func():
    import asyncio
    await asyncio.sleep(0.1)
    return 42

@pytest.mark.asyncio
async def test_async_happy_path(wrapped_func):
    async def async_wrapper(func):
        try:
            return await func()
        except Exception as e:
            # Log the exception
            logging.error(f"Error occurred in {func.__name__}: {str(e)}")
            # Optionally re-raise the exception if needed
            raise

    wrapped_async_func = wrapper(async_mock_func)
    result = await wrapped_async_func()
    assert result == 42

def test_error_case_with_exception(wrapped_func):
    def error_func():
        raise ValueError("Invalid input")
    
    wrapped_error_func = wrapper(error_func)
    with pytest.raises(ValueError) as exc_info:
        wrapped_error_func()
    assert str(exc_info.value) == "ValueError: Invalid input"