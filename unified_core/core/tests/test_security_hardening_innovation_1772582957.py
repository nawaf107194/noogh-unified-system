import pytest
import hashlib
from pathlib import Path

def test_get_hash_valid_file(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")
    
    expected_hash = hashlib.sha256("test".encode()).hexdigest()
    result = _get_hash(str(test_file))
    
    assert result == expected_hash

def test_get_hash_empty_file(tmp_path):
    test_file = tmp_path / "empty.txt"
    test_file.touch()
    
    expected_hash = hashlib.sha256(b"").hexdigest()
    result = _get_hash(str(test_file))
    
    assert result == expected_hash

def test_get_hash_nonexistent_file(tmp_path):
    test_file = tmp_path / "nonexistent.txt"
    result = _get_hash(str(test_file))
    assert result == ""

def test_get_hash_none_path():
    result = _get_hash(None)
    assert result == ""