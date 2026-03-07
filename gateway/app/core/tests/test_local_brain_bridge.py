import pytest
from unittest.mock import Mock
from gateway.app.core.local_brain_bridge import set_default

# Mocking the logger to avoid actual logging during tests
logger = Mock()

def test_set_default_happy_path():
    """Test with normal inputs where value is provided."""
    result = set_default(10, 5, "Value is missing")
    assert result == 10

def test_set_default_with_empty_string():
    """Test with an empty string as value."""
    result = set_default("", 5, "Value is missing")
    assert result == 5
    logger.warning.assert_called_once_with("Value is missing")

def test_set_default_with_none():
    """Test with None as value."""
    result = set_default(None, 5, "Value is missing")
    assert result == 5
    logger.warning.assert_called_once_with("Value is missing")

def test_set_default_with_zero():
    """Test with zero as value."""
    result = set_default(0, 5, "Value is missing")
    assert result == 0

def test_set_default_with_false():
    """Test with False as value."""
    result = set_default(False, 5, "Value is missing")
    assert result == 5
    logger.warning.assert_called_once_with("Value is missing")

def test_set_default_with_invalid_input_type():
    """Test with invalid input type (non-boolean and non-null)."""
    with pytest.raises(TypeError):
        set_default([], 5, "Value is missing")

# Since the function does not have any asynchronous behavior, no async tests are necessary.