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
        decoded_lines = [line.decode("utf-8", "replace") for line in data.splitlines()]
        for line in decoded_lines[-n:]:
            if "/uc3/chat" not in line and "POST /api/v1/process" not in line:
                lines.append(line)
        return "\n".join(lines)

def test_read_last_lines_happy_path():
    # Create a temporary file with some content
    temp_file = Path("temp_test.txt")
    with open(temp_file, "w") as f:
        f.write("Line 1\nLine 2\nLine 3\n")

    result = read_last_lines(str(temp_file))
    assert result == "Line 2\nLine 3"

def test_read_last_lines_empty_file():
    temp_file = Path("temp_test.txt")
    with open(temp_file, "w") as f:
        pass

    result = read_last_lines(str(temp_file))
    assert result == ""

def test_read_last_lines_none_path():
    result = read_last_lines(None)
    assert result == ""

def test_read_last_lines_invalid_path():
    # This should not raise an exception; it will just return an empty string
    result = read_last_lines("nonexistent_file.txt")
    assert result == ""

def test_read_last_lines_boundary_n():
    temp_file = Path("temp_test.txt")
    with open(temp_file, "w") as f:
        f.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")

    result = read_last_lines(str(temp_file), n=3)
    assert result == "Line 3\nLine 4\nLine 5"

def test_read_last_lines_filter_lines():
    temp_file = Path("temp_test.txt")
    with open(temp_file, "w") as f:
        f.write("Line 1\n/uc3/chat: Line 2\nPOST /api/v1/process: Line 3\nLine 4")

    result = read_last_lines(str(temp_file))
    assert result == "Line 1\nLine 4"

def test_read_last_lines_large_file():
    temp_file = Path("temp_test.txt")
    with open(temp_file, "w") as f:
        for i in range(1000):
            f.write(f"Line {i}\n")

    result = read_last_lines(str(temp_file), n=200)
    assert len(result.splitlines()) == 200

def test_read_last_lines_binary_file():
    temp_file = Path("temp_test.bin")
    with open(temp_file, "wb") as f:
        f.write(b"Binary data\n")

    result = read_last_lines(str(temp_file))
    assert result == ""

def teardown_module():
    # Clean up temporary files
    for file in ["temp_test.txt", "temp_test.bin"]:
        if Path(file).exists():
            Path(file).unlink()