import pytest
from unittest.mock import MagicMock, mock_open
from pathlib import Path
import hashlib

# Mock the sha256_file function to test it
def sha256_file(p: Path, max_bytes: int = 5_000_000) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        remaining = max_bytes
        while remaining > 0:
            chunk = f.read(min(65536, remaining))
            if not chunk:
                break
            h.update(chunk)
            remaining -= len(chunk)
    return h.hexdigest()

@pytest.fixture
def mock_path():
    class MockPath(Path):
        def open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
            return mock_open(read_data=self.data)(mode)
    return MockPath

def test_sha256_file_happy_path(mock_path):
    # Create a mock file with known content
    mock_path.data = b"Hello World"
    p = mock_path("/path/to/file")
    expected_hash = hashlib.sha256(b"Hello World").hexdigest()
    assert sha256_file(p) == expected_hash

def test_sha256_file_empty_file(mock_path):
    # Test with an empty file
    mock_path.data = b""
    p = mock_path("/path/to/empty_file")
    expected_hash = hashlib.sha256(b"").hexdigest()
    assert sha256_file(p) == expected_hash

def test_sha256_file_none_path():
    # Test with None path
    with pytest.raises(TypeError):
        sha256_file(None)

def test_sha256_file_large_file(mock_path):
    # Test with a large file that exceeds max_bytes
    mock_path.data = b"A" * 5_000_001
    p = mock_path("/path/to/large_file")
    expected_hash = hashlib.sha256(b"A" * 5_000_000).hexdigest()
    assert sha256_file(p) == expected_hash

def test_sha256_file_invalid_max_bytes(mock_path):
    # Test with invalid max_bytes
    mock_path.data = b"Test data"
    p = mock_path("/path/to/invalid_max_bytes")
    with pytest.raises(ValueError):
        sha256_file(p, max_bytes=-1)

def test_sha256_file_nonexistent_file():
    # Test with a non-existent file
    p = Path("/path/to/nonexistent_file")
    with pytest.raises(FileNotFoundError):
        sha256_file(p)

def test_sha256_file_read_error(mock_path):
    # Simulate a read error from the file
    mock_path.data = b"Data"
    p = mock_path("/path/to/error_file")
    p.open = MagicMock(side_effect=IOError("Simulated I/O error"))
    with pytest.raises(IOError):
        sha256_file(p)