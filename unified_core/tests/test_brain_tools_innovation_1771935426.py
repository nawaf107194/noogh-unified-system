import pytest
from pathlib import Path
from unified_core.brain_tools import read_file

def test_read_file_happy_path():
    # Prepare a sample file
    temp_file = Path("temp_test_file.txt")
    temp_file.write_text("Hello, world!\nThis is a test.")
    
    result = read_file(str(temp_file))
    
    assert result == {
        "success": True,
        "path": str(temp_file),
        "content": "Hello, world!\nThis is a test.",
        "size_bytes": 26,
        "lines": 3,
        "truncated": False
    }
    
    # Clean up the temporary file
    temp_file.unlink()

def test_read_file_empty_path():
    result = read_file("")
    
    assert result == {
        "success": False,
        "error": "الملف غير موجود: "
    }

def test_read_file_nonexistent_path():
    result = read_file("path/to/nonexistent/file.txt")
    
    assert result == {
        "success": False,
        "error": "الملف غير موجود: path/to/nonexistent/file.txt"
    }

def test_read_file_max_bytes():
    temp_file = Path("temp_test_file_large.txt")
    temp_file.write_text("a" * 60000)
    
    result = read_file(str(temp_file), max_bytes=50000)
    
    assert result == {
        "success": True,
        "path": str(temp_file),
        "content": "a" * 50000 + "...",
        "size_bytes": 60000,
        "lines": 1,
        "truncated": True
    }
    
    # Clean up the temporary file
    temp_file.unlink()

def test_read_file_encoding_error():
    temp_file = Path("temp_test_file_encoding.txt")
    temp_file.write_text("\xff")
    
    result = read_file(str(temp_file), encoding="utf-8")
    
    assert result == {
        "success": True,
        "path": str(temp_file),
        "content": "",
        "size_bytes": 1,
        "lines": 0,
        "truncated": False
    }
    
    # Clean up the temporary file
    temp_file.unlink()