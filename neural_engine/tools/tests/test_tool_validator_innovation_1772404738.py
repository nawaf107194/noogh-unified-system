import pytest

from neural_engine.tools.tool_validator import sanitize_path, ValidationError

def test_sanitize_path_happy_path():
    # Normal input with no issues
    assert sanitize_path("subdir/file.txt") == "subdir/file.txt"
    assert sanitize_path("/home/noogh/subdir/file.txt") == "/home/noogh/subdir/file.txt"

def test_sanitize_path_edge_cases():
    # Edge case: empty string
    with pytest.raises(ValidationError):
        sanitize_path("")
    
    # Edge case: None
    with pytest.raises(ValidationError):
        sanitize_path(None)
    
    # Edge case: boundary conditions (length, characters)
    assert sanitize_path("/home/noogh/subdir/file.txt") == "/home/noogh/subdir/file.txt"

def test_sanitize_path_error_cases():
    # Error case: null byte in path
    with pytest.raises(ValidationError):
        sanitize_path("subdir/file\x00.txt")
    
    # Error case: parent directory references
    with pytest.raises(ValidationError):
        sanitize_path("subdir/../file.txt")
    
    # Error case: absolute path not in allowed roots
    with pytest.raises(ValidationError):
        sanitize_path("/etc/passwd")

def test_sanitize_path_async_behavior():
    # Since the function is synchronous, there's no async behavior to test
    pass