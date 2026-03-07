import pytest

from unified_core.evolution.diff_parser import _parse_noogh_format, logger

def test_parse_noogh_format_happy_path():
    diff = """--- ORIGINAL ---
def old_function(x):
    return x * 2

+++ REFACTORED +++
def new_function(x):
    return x * 3
"""
    expected_output = {
        "original_code": "def old_function(x):\n    return x * 2",
        "refactored_code": "def new_function(x):\n    return x * 3",
        "function": "unknown",
        "confidence": 0.8,
    }
    assert _parse_noogh_format(diff) == expected_output

def test_parse_noogh_format_missing_markers():
    diff = "Some random text"
    assert _parse_noogh_format(diff) is None

def test_parse_noogh_format_empty_original_code():
    diff = """--- ORIGINAL ---
def old_function(x):
    return x * 2

+++ REFACTORED +++
"""
    assert _parse_noogh_format(diff) is None

def test_parse_noogh_format_empty_refactored_code():
    diff = """--- ORIGINAL ---
def old_function(x):
    return x * 2

+++ REFACTORED +++
def new_function(x):
    return x * 3
"""
    assert _parse_noogh_format(diff) is None

def test_parse_noogh_format_invalid_confidence():
    diff = """--- ORIGINAL ---
def old_function(x):
    return x * 2

+++ REFACTORED +++
def new_function(x):
    return x * 3
# Confidence: invalid
"""
    expected_output = {
        "original_code": "def old_function(x):\n    return x * 2",
        "refactored_code": "def new_function(x):\n    return x * 3",
        "function": "unknown",
        "confidence": 0.8,
    }
    assert _parse_noogh_format(diff) == expected_output

def test_parse_noogh_format_no_confidence():
    diff = """--- ORIGINAL ---
def old_function(x):
    return x * 2

+++ REFACTORED +++
def new_function(x):
    return x * 3
# Refactoring: some_function
"""
    expected_output = {
        "original_code": "def old_function(x):\n    return x * 2",
        "refactored_code": "def new_function(x):\n    return x * 3",
        "function": "some_function",
        "confidence": 0.8,
    }
    assert _parse_noogh_format(diff) == expected_output

def test_parse_noogh_format_no_refactoring_header():
    diff = """--- ORIGINAL ---
def old_function(x):
    return x * 2

+++ REFACTORED +++
def new_function(x):
    return x * 3
"""
    expected_output = {
        "original_code": "def old_function(x):\n    return x * 2",
        "refactored_code": "def new_function(x):\n    return x * 3",
        "function": "unknown",
        "confidence": 0.8,
    }
    assert _parse_noogh_format(diff) == expected_output

def test_parse_noogh_format_no_original_header():
    diff = """+++ REFACTORED +++
def new_function(x):
    return x * 3
# Refactoring: some_function
# Confidence: 90%
"""
    expected_output = {
        "original_code": "",
        "refactored_code": "def new_function(x):\n    return x * 3",
        "function": "some_function",
        "confidence": 0.9,
    }
    assert _parse_noogh_format(diff) == expected_output

def test_parse_noogh_format_no_refactored_header():
    diff = """--- ORIGINAL ---
def old_function(x):
    return x * 2
# Refactoring: some_function
# Confidence: 90%
"""
    expected_output = {
        "original_code": "def old_function(x):\n    return x * 2",
        "refactored_code": "",
        "function": "some_function",
        "confidence": 0.9,
    }
    assert _parse_noogh_format(diff) == expected_output

def test_parse_noogh_format_all_empty():
    diff = ""
    assert _parse_noogh_format(diff) is None