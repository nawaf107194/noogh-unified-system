import pytest

from runpod_teacher.architecture_1771624450 import save_data

def test_save_data_happy_path(tmp_path):
    # Test with normal string data
    file_path = tmp_path / "test_file.txt"
    data = "Hello, World!"
    save_data(data, file_path)
    
    assert file_path.read_text() == data

def test_save_data_empty_string(tmp_path):
    # Test with empty string
    file_path = tmp_path / "empty_file.txt"
    data = ""
    save_data(data, file_path)
    
    assert file_path.read_text() == data

def test_save_data_none_data(tmp_path):
    # Test with None as data
    file_path = tmp_path / "none_data_file.txt"
    data = None
    
    with pytest.raises(TypeError):
        save_data(data, file_path)

def test_save_data_non_string_data(tmp_path):
    # Test with non-string data (e.g., list)
    file_path = tmp_path / "non_string_file.txt"
    data = [1, 2, 3]
    
    with pytest.raises(TypeError):
        save_data(data, file_path)

def test_save_data_invalid_file_path(tmp_path):
    # Test with an invalid file path
    file_path = "/invalid/path/to/file.txt"
    data = "Test Data"
    
    with pytest.raises(IOError):
        save_data(data, file_path)

# Since the function is synchronous and does not involve async behavior,
# there are no tests for async behavior.