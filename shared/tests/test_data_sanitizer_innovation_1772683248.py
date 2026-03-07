import pytest
from src.shared.data_sanitizer import DataSanitizer

def test_sanitize_list_happy_path():
    test_data = ["hello", 123, 45.67]
    expected = [
        DataSanitizer.sanitize_string("hello"),
        DataSanitizer.sanitize_number(123),
        DataSanitizer.sanitize_number(45.67)
    ]
    assert DataSanitizer.sanitize_list(test_data) == expected

def test_sanitize_list_empty_list():
    assert DataSanitizer.sanitize_list([]) == []

def test_sanitize_list_with_none():
    test_data = [None]
    assert DataSanitizer.sanitize_list(test_data) == [None]

def test_sanitize_list_edge_cases():
    # Test with boundary values
    min_int = -1e20
    max_int = 1e20
    min_float = 1e308
    max_float = -1e308
    
    test_data = [min_int, max_int, min_float, max_float, None]
    result = DataSanitizer.sanitize_list(test_data)
    
    # Verify None is preserved
    assert result[-1] is None
    
    # Verify numerical boundaries are sanitized
    assert all(isinstance(item, (int, float)) for item in result[:4])

def test_sanitize_list_error_cases():
    # Test with unsupported types
    test_data = [True, {"key": "value"}]
    result = DataSanitizer.sanitize_list(test_data)
    
    # Verify original items are returned
    assert result == test_data

def test_sanitize_list_mixed_types():
    test_data = ["hello", 123, 45.67, None, True]
    result = DataSanitizer.sanitize_list(test_data)
    
    # Verify strings and numbers are sanitized, others are preserved
    assert result[0] == DataSanitizer.sanitize_string("hello")
    assert result[1] == DataSanitizer.sanitize_number(123)
    assert result[2] == DataSanitizer.sanitize_number(45.67)
    assert result[3] is None
    assert result[4] is True