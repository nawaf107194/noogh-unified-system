import pytest
from neural_engine.tools.tool_executor import _safe_file_exists

def test_safe_file_exists_happy_path():
    # Happy path with a valid file
    result = _safe_file_exists("/path/to/existing/file.txt")
    assert result == {"success": True, "result": "exists"}

def test_safe_file_exists_empty_path():
    # Edge case: empty path
    result = _safe_file_exists("")
    assert result == {"success": False, "error": "path required"}

def test_safe_file_exists_none_path():
    # Edge case: None as path
    result = _safe_file_exists(None)
    assert result == {"success": False, "error": "path required"}

def test_safe_file_exists_nonexistent_file():
    # Normal input with a non-existent file
    result = _safe_file_exists("/path/to/nonexistent/file.txt")
    assert result == {"success": True, "result": "not found"}

# Assuming _validate_path and _os.path.exists are the only functions called,
# we don't need to mock them for these tests as they are part of the tested function.
# If _validate_path or _os.path.exists were external dependencies, we would use mocking.