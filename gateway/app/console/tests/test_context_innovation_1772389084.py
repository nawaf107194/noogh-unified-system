import pytest
from unittest.mock import patch, mock_open
from pathlib import Path

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
        decoded_lines = [line.decode("utf-8", "replace") for line in data.splitlines()]
        for line in decoded_lines[-n:]:
            if "/uc3/chat" not in line and "POST /api/v1/process" not in line:
                lines.append(line)
        return "\n".join(lines)

def test_read_last_lines_happy_path():
    with patch('builtins.open', mock_open(read_data="line1\nline2\nline3")) as mock_file:
        result = read_last_lines("test.txt", 2)
        assert result == "line2\nline3"

def test_read_last_lines_edge_case_empty_file():
    with patch('builtins.open', mock_open(read_data="")) as mock_file:
        result = read_last_lines("empty.txt", 2)
        assert result == ""

def test_read_last_lines_edge_case_none_path():
    with pytest.raises(FileNotFoundError):
        read_last_lines(None)

def test_read_last_lines_edge_case_non_existent_path():
    with pytest.raises(FileNotFoundError):
        read_last_lines("nonexistent.txt")

def test_read_last_lines_error_case_invalid_n_type():
    with pytest.raises(TypeError):
        read_last_lines("test.txt", "invalid")

def test_read_last_lines_boundary_case_small_n():
    with patch('builtins.open', mock_open(read_data="line1\nline2\nline3")) as mock_file:
        result = read_last_lines("test.txt", 1)
        assert result == "line3"

def test_read_last_lines_boundary_case_large_n():
    with patch('builtins.open', mock_open(read_data="line1\nline2\nline3")) as mock_file:
        result = read_last_lines("test.txt", 5)
        assert result == "line1\nline2\nline3"