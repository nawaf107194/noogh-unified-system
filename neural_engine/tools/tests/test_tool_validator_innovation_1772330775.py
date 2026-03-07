import os
import pytest

from neural_engine.tools.tool_validator import sanitize_path, ValidationError

def test_sanitize_path_happy_path():
    # Normal inputs
    assert sanitize_path("folder/subfolder/file.txt") == "folder/subfolder/file.txt"
    assert sanitize_path("/home/noogh/projects/file.txt") == "/home/noogh/projects/file.txt"

def test_sanitize_path_edge_cases():
    # Empty string
    with pytest.raises(ValidationError):
        sanitize_path("")
    
    # None value
    with pytest.raises(ValidationError):
        sanitize_path(None)
    
    # Boundary cases (just under and over boundaries)
    boundary = "/var/noogh"
    assert sanitize_path(boundary) == boundary
    
def test_sanitize_path_error_cases():
    # Null bytes
    with pytest.raises(ValidationError):
        sanitize_path("folder\0subfolder/file.txt")
    
    # Parent directory traversal
    with pytest.raises(ValidationError):
        sanitize_path("folder/../file.txt")
    
    # Absolute path not in allowed roots
    with pytest.raises(ValidationError):
        sanitize_path("/home/otheruser/projects/file.txt")

def test_sanitize_path_async_behavior():
    # Asynchronous behavior is not applicable here as the function is synchronous
    pass