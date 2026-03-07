import pytest
from unified_core.evolution.diff_parser import extract_metadata_from_diff

def test_extract_metadata_noogh_format():
    diff = """# Refactoring: my_function
    # Confidence: 90%
    --- ORIGINAL ---
    def old_function(x):
        return x + 1
    
    +++ REFACTORED +++
    def new_function(x):
        return x + 2"""
    expected = {
        "original_code": 'def old_function(x):\n    return x + 1',
        "refactored_code": 'def new_function(x):\n    return x + 2'
    }
    assert extract_metadata_from_diff(diff) == expected

def test_extract_metadata_unified_diff_format():
    diff = """--- a/path/to/file
    +++ b/path/to/file
    @@ -1,3 +1,3 @@
    def old_function(x):
        return x + 1
    
    -def new_function(x):
    -    return x + 2
    +def new_function(x):
    +    return x + 3"""
    expected = {
        "original_code": 'def old_function(x):\n    return x + 1\n-def new_function(x):\n-    return x + 2',
        "refactored_code": 'def old_function(x):\n    return x + 1\n+def new_function(x):\n+    return x + 3'
    }
    assert extract_metadata_from_diff(diff) == expected

def test_extract_metadata_empty_diff():
    diff = ""
    assert extract_metadata_from_diff(diff) is None

def test_extract_metadata_none_diff():
    diff = None
    assert extract_metadata_from_diff(diff) is None

def test_extract_metadata_no_matching_format():
    diff = """--- a/path/to/file
    +++ b/path/to/file
    @@ -1,3 +1,3 @@
    def old_function(x):
        return x + 1"""
    assert extract_metadata_from_diff(diff) is None

def test_extract_metadata_invalid_diff_format():
    diff = "Invalid format"
    assert extract_metadata_from_diff(diff) is None