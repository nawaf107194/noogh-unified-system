import pytest
from pathlib import Path
import os

def read_last_lines(path: str, n: int = 200) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    with p.open("rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        block = 4096
        data = b""
        while size > 0 and data.count(b"\n") <= n:
            step = min(block, size)
            size -= step
            f.seek(size)
            data = f.read(step) + data
        lines = []
        # Filter logic to prevent chat history loops
        decoded_lines = [line.decode("utf-8", "replace") for line in data.splitlines()]
        for line in decoded_lines[-n:]:
            if "/uc3/chat" not in line and "POST /api/v1/process" not in line:
                lines.append(line)
        return "\n".join(lines)

# Tests
def test_read_last_lines_happy_path(tmp_path):
    content = """line1\nline2\nline3"""
    file_path = tmp_path / "test.txt"
    with open(file_path, 'w') as f:
        f.write(content)
    
    result = read_last_lines(str(file_path), n=2)
    assert result == "line2\nline3"

def test_read_last_lines_empty_file(tmp_path):
    file_path = tmp_path / "empty.txt"
    with open(file_path, 'w'):
        pass
    
    result = read_last_lines(str(file_path))
    assert result == ""

def test_read_last_lines_none_path():
    result = read_last_lines(None)
    assert result == ""

def test_read_last_lines_invalid_path(tmp_path):
    invalid_path = tmp_path / "nonexistent.txt"
    if not invalid_path.exists():
        with pytest.raises(FileNotFoundError):
            read_last_lines(str(invalid_path))

def test_read_last_lines_boundary_case(tmp_path):
    content = "\n".join(f"line{i}" for i in range(500))
    file_path = tmp_path / "boundary.txt"
    with open(file_path, 'w') as f:
        f.write(content)
    
    result = read_last_lines(str(file_path), n=200)
    assert len(result.splitlines()) == 200

def test_read_last_lines_filtering(tmp_path):
    content = """line1\n/uc3/chat\nline3\nPOST /api/v1/process"""
    file_path = tmp_path / "filter.txt"
    with open(file_path, 'w') as f:
        f.write(content)
    
    result = read_last_lines(str(file_path), n=2)
    assert result == "line3"

def test_read_last_lines_large_file(tmp_path):
    content = "\n".join(f"line{i}" for i in range(1000))
    file_path = tmp_path / "large.txt"
    with open(file_path, 'w') as f:
        f.write(content)
    
    result = read_last_lines(str(file_path), n=500)
    assert len(result.splitlines()) == 500