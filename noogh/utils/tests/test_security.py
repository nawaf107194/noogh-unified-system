import pytest
from noogh.utils.security import secure_find

def test_happy_path():
    result = secure_find("/tmp", "test*", max_results=5, timeout=10)
    assert result[0] is True
    assert len(result[1]) > 0 or (result[1] == "No files found")

def test_empty_directory():
    result = secure_find("/empty_dir", "*.txt", max_results=5, timeout=10)
    assert result[0] is False
    assert result[1].startswith("Error: Directory not found")

def test_invalid_path_traversal():
    result = secure_find("/tmp/../etc", "test*", max_results=5, timeout=10)
    assert result[0] is False
    assert result[1] == "Security Error: Invalid filename - path traversal detected"

def test_invalid_name_pattern():
    result = secure_find("/tmp", "*.txt; rm -rf /", max_results=5, timeout=10)
    assert result[0] is False
    assert result[1].startswith("SECURITY: Path traversal blocked in find")

def test_timeout():
    result = secure_find("/tmp", "test*", max_results=5, timeout=0.01)
    assert result[0] is False
    assert result[1] == "Timeout: Find command took too long"

def test_max_results():
    result = secure_find("/tmp", "*.txt", max_results=3, timeout=10)
    lines = result[1].strip().split('\n')
    assert len(lines) <= 3