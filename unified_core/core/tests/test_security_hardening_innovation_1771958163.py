import pytest
from unified_core.core.security_hardening import _get_hash

def test_get_hash_happy_path(tmpdir):
    content = b"test content"
    file_path = str(tmpdir.join("test.txt"))
    with open(file_path, "wb") as f:
        f.write(content)
    
    assert _get_hash(file_path) == hashlib.sha256(content).hexdigest()

def test_get_hash_empty_file(tmpdir):
    file_path = str(tmpdir.join("empty.txt"))
    with open(file_path, "wb"):
        pass
    
    assert _get_hash(file_path) == hashlib.sha256(b"").hexdigest()

def test_get_hash_none_input():
    assert _get_hash(None) == ""

def test_get_hash_invalid_path(tmpdir):
    invalid_path = str(tmpdir.join("nonexistent.txt"))
    
    assert _get_hash(invalid_path) == ""