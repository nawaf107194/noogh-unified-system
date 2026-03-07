import pytest
from typing import Optional, Dict, Any
from ..diff_parser import extract_metadata_from_diff

@pytest.mark.parametrize("test_case", [
    # Happy path - NOOGH format
    {
        "input": (
            "# Refactoring: test_function\n"
            "# Confidence: 90%\n"
            "--- ORIGINAL ---\n"
            "def test_function():\n"
            "    pass\n"
            "+++ REFACTORED +++\n"
            "def test_function():\n"
            "    return None\n"
        ),
        "expected": {
            "original_code": "def test_function():\n    pass\n",
            "refactored_code": "def test_function():\n    return None\n"
        }
    },
    
    # Happy path - unified diff format
    {
        "input": (
            "--- a/file.py\n"
            "+++ b/file.py\n"
            "@@ -1,4 +1,4 @@\n"
            " def test_function():\n"
            "-    pass\n"
            "+    return None\n"
        ),
        "expected": {
            "original_code": " def test_function():\n-    pass\n",
            "refactored_code": " def test_function():\n+    return None\n"
        }
    },
    
    # Edge case - empty input
    {
        "input": "",
        "expected": None
    },
    
    # Edge case - None input
    {
        "input": None,
        "expected": None
    },
    
    # Edge case - minimal NOOGH format
    {
        "input": (
            "--- ORIGINAL ---\n"
            "original\n"
            "+++ REFACTORED +++\n"
            "refactored\n"
        ),
        "expected": {
            "original_code": "original\n",
            "refactored_code": "refactored\n"
        }
    },
    
    # Error case - invalid unified diff format
    {
        "input": (
            "--- a/file.py\n"
            "+++ b/file.py\n"
            "invalid diff content\n"
        ),
        "expected": None
    },
    
    # Error case - invalid NOOGH format
    {
        "input": (
            "# Refactoring: test_function\n"
            "--- ORIGINAL ---\n"
            "original\n"
            # Missing refactored section
        ),
        "expected": None
    }
])
def test_extract_metadata_from_diff(test_case):
    result = extract_metadata_from_diff(test_case["input"])
    if test_case["expected"] is None:
        assert result is None
    else:
        assert result is not None
        assert result["original_code"] == test_case["expected"]["original_code"]
        assert result["refactored_code"] == test_case["expected"]["refactored_code"]