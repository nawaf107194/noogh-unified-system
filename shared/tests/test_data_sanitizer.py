import pytest
from shared.data_sanitizer import sanitize_dict, DataSanitizer

def test_sanitize_dict_happy_path():
    data = {
        "name": "John Doe",
        "age": 30,
        "scores": [95, 85, 75],
        "details": {"height": 180, "weight": 75}
    }
    expected_output = {
        "name": "John Doe",
        "age": 30,
        "scores": [95, 85, 75],
        "details": {"height": 180, "weight": 75}
    }
    assert sanitize_dict(data) == expected_output

def test_sanitize_dict_empty_input():
    data = {}
    expected_output = {}
    assert sanitize_dict(data) == expected_output

def test_sanitize_dict_none_input():
    data = None
    expected_output = None
    assert sanitize_dict(data) is expected_output

def test_sanitize_dict_boundary_values():
    data = {
        "min_age": 1,
        "max_age": 120,
        "scores": [0, 100]
    }
    expected_output = {
        "min_age": 1,
        "max_age": 120,
        "scores": [0, 100]
    }
    assert sanitize_dict(data) == expected_output

def test_sanitize_dict_invalid_string():
    data = {
        "name": "John Doe\x00"
    }
    expected_output = {
        "name": "John Doe"
    }
    assert sanitize_dict(data) == expected_output

def test_sanitize_dict_invalid_number():
    data = {
        "age": float('inf')
    }
    expected_output = {
        "age": None
    }
    assert sanitize_dict(data) == expected_output

def test_sanitize_dict_invalid_list():
    data = {
        "scores": [105, 85]
    }
    expected_output = {
        "scores": [None, 85]
    }
    assert sanitize_dict(data) == expected_output

def test_sanitize_dict_invalid_dict():
    data = {
        "details": {"height": -1}
    }
    expected_output = {
        "details": {"height": None}
    }
    assert sanitize_dict(data) == expected_output