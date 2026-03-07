import pytest

from neural_engine.error_handling_decorator import handle_errors

def test_handle_errors_happy_path():
    @handle_errors
    def add(a, b):
        return a + b
    
    result = add(2, 3)
    assert result == 5

def test_handle_errors_edge_case_none_input():
    @handle_errors
    def check_none(x):
        if x is None:
            raise ValueError("Input cannot be None")
    
    with pytest.raises(ValueError) as exc_info:
        check_none(None)
    assert "Input cannot be None" in str(exc_info.value)

def test_handle_errors_error_case_invalid_input():
    @handle_errors
    def divide(a, b):
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
    
    with pytest.raises(ZeroDivisionError) as exc_info:
        divide(10, 0)
    assert "Cannot divide by zero" in str(exc_info.value)