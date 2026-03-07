import pytest

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def test_read_file_happy_path(tmp_path):
    content = "Hello, world!"
    file_path = tmp_path / "test.txt"
    file_path.write_text(content)
    
    result = read_file(file_path)
    assert result == content

def test_read_file_empty_file(tmp_path):
    file_path = tmp_path / "empty.txt"
    file_path.touch()
    
    result = read_file(file_path)
    assert result == ""

def test_read_file_none_input():
    with pytest.raises(ValueError) as exc_info:
        read_file(None)
    assert str(exc_info.value) == "File path cannot be None"

def test_read_file_invalid_path(capsys, tmp_path):
    file_path = tmp_path / "non_existent.txt"
    
    result = read_file(file_path)
    assert result is None
    captured = capsys.readouterr()
    assert "Error reading file" in captured.err

# Assuming the function does not support async behavior