import pytest

from gateway.app.core.validation import ensure_string_not_empty, ValidationError

def test_ensure_string_not_empty_happy_path():
    ensure_string_not_empty("test")

def test_ensure_string_not_empty_strip():
    ensure_string_not_empty("   ")

def test_ensure_string_not_empty_none():
    with pytest.raises(ValidationError) as exc_info:
        ensure_string_not_empty(None)
    assert str(exc_info.value) == "value cannot be empty"

def test_ensure_string_not_empty_empty_str():
    with pytest.raises(ValidationError) as exc_info:
        ensure_string_not_empty("")
    assert str(exc_info.value) == "value cannot be empty"

def test_ensure_string_not_empty_invalid_input():
    with pytest.raises(ValueError):
        ensure_string_not_empty(123)