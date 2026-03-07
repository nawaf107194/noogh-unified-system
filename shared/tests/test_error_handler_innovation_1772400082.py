import pytest

from shared.error_handler import ErrorHandler

@pytest.fixture
def error_handler():
    return ErrorHandler()

def test_happy_path(error_handler):
    # Define a custom exception for testing
    class CustomException(Exception):
        pass
    
    # Create an instance of the custom exception
    error = CustomException("Test error")
    
    with pytest.raises(CustomException) as exc_info:
        error_handler.raise_and_log(error, "Additional message")
    
    # Check if the error was raised correctly
    assert str(exc_info.value) == "Test error"

def test_edge_cases_empty_error(error_handler):
    with pytest.raises(ValueError) as exc_info:
        error_handler.raise_and_log(None)
    
    assert str(exc_info.value) == "Invalid error instance: None"

def test_edge_cases_none_message(error_handler):
    # Define a custom exception for testing
    class CustomException(Exception):
        pass
    
    # Create an instance of the custom exception
    error = CustomException("Test error")
    
    with pytest.raises(CustomException) as exc_info:
        error_handler.raise_and_log(error, None)
    
    # Check if the error was raised correctly
    assert str(exc_info.value) == "Test error"

def test_error_cases_invalid_input(error_handler):
    with pytest.raises(TypeError) as exc_info:
        error_handler.raise_and_log("Not an exception", "Additional message")
    
    assert str(exc_info.value) == "Invalid error instance: 'str'"