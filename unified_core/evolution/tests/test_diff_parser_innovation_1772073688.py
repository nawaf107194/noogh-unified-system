import pytest

from unified_core.evolution.diff_parser import _parse_noogh_format

def test_parse_noogh_format_happy_path():
    diff = """--- ORIGINAL ---
def old_function(x):
    return x + 1

+++ REFACTORED +++
def new_function(x):
    return x + 2

# Refactoring: new_function
# Confidence: 90%
"""
    result = _parse_noogh_format(diff)
    assert result == {
        "original_code": "def old_function(x):\n    return x + 1",
        "refactored_code": "def new_function(x):\n    return x + 2",
        "function": "new_function",
        "confidence": 0.9
    }

def test_parse_noogh_format_empty_diff():
    result = _parse_noogh_format("")
    assert result is None

def test_parse_noogh_format_none_diff():
    result = _parse_noogh_format(None)
    assert result is None

def test_parse_noogh_format_missing_markers():
    diff = """--- ORIGINAL ---
def old_function(x):
    return x + 1
"""
    result = _parse_noogh_format(diff)
    assert result is None

    diff = """+++ REFACTORED +++
def new_function(x):
    return x + 2
"""
    result = _parse_noogh_format(diff)
    assert result is None

def test_parse_noogh_format_empty_codes():
    diff = """--- ORIGINAL ---
  
+++ REFACTORED +++
  

# Refactoring: new_function
# Confidence: 90%
"""
    result = _parse_noogh_format(diff)
    assert result is None

def test_parse_noogh_format_invalid_confidence():
    diff = """--- ORIGINAL ---
def old_function(x):
    return x + 1

+++ REFACTORED +++
def new_function(x):
    return x + 2

# Refactoring: new_function
# Confidence: invalid_value%
"""
    result = _parse_noogh_format(diff)
    assert result == {
        "original_code": "def old_function(x):\n    return x + 1",
        "refactored_code": "def new_function(x):\n    return x + 2",
        "function": "unknown",
        "confidence": 0.8
    }