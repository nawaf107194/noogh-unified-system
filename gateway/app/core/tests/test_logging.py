import pytest

from gateway.app.core.logging import get_log_context, _log_context_var

# Happy path (normal inputs)
def test_get_log_context_happy_path():
    # Arrange
    expected_context = {"key": "value"}
    _log_context_var.set(expected_context)

    # Act
    result = get_log_context()

    # Assert
    assert result == expected_context, f"Expected {expected_context}, but got {result}"

# Edge cases (empty, None)
def test_get_log_context_empty():
    # Arrange
    _log_context_var.set({})

    # Act
    result = get_log_context()

    # Assert
    assert result == {}, "Expected an empty dictionary, but got a non-empty one"

def test_get_log_context_none():
    # Arrange
    _log_context_var.set(None)

    # Act
    result = get_log_context()

    # Assert
    assert result is None, "Expected None, but got a non-None value"

# Error cases (invalid inputs) - This function does not raise exceptions, so no error case tests

# Async behavior (if applicable) - This function does not have any async behavior, so no async test