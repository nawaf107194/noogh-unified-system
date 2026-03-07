import pytest

from gateway.app.core.validation import ensure_string_not_empty, ValidationError

def test_ensure_string_not_empty_happy_path():
    # Test normal input
    try:
        ensure_string_not_empty("Hello")
    except ValidationError as e:
        assert False, f"Unexpected error: {e}"

def test_ensure_string_not_empty_edge_cases():
    # Test empty string
    with pytest.raises(ValidationError) as exc_info:
        ensure_string_not_empty("")
    assert "value cannot be empty" in str(exc_info.value)

    # Test None
    with pytest.raises(ValidationError) as exc_info:
        ensure_string_not_empty(None)
    assert "value cannot be empty" in str(exc_info.value)

    # Test string with only whitespace
    with pytest.raises(ValidationError) as exc_info:
        ensure_string_not_empty("   ")
    assert "value cannot be empty" in str(exc_info.value)

def test_ensure_string_not_empty_error_cases():
    # Test invalid input type
    with pytest.raises(TypeError):
        ensure_string_not_empty(123)