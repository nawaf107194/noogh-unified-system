import pytest

def load_config(file_path):
    """Load configuration from a file."""
    with open(file_path, 'r') as config_file:
        return config_file.read()

# Happy path test case
def test_load_config_happy_path(tmpdir):
    # Create a temporary configuration file
    file_content = "key1=value1\nkey2=value2"
    temp_file = tmpdir.join("config.txt")
    temp_file.write(file_content)
    
    # Call the function with the temporary file path
    result = load_config(temp_file.strpath)
    
    # Assert that the function returns the expected content
    assert result == file_content

# Edge case test cases
def test_load_config_empty_file(tmpdir):
    # Create an empty configuration file
    temp_file = tmpdir.join("config.txt")
    temp_file.write("")
    
    # Call the function with the temporary file path
    result = load_config(temp_file.strpath)
    
    # Assert that the function returns an empty string
    assert result == ""

def test_load_config_none_input():
    # Call the function with None as input
    result = load_config(None)
    
    # Assert that the function returns None
    assert result is None

# Error case test cases
def test_load_config_invalid_file_path():
    # Call the function with a non-existent file path
    with pytest.raises(FileNotFoundError):
        load_config("non_existent_file.txt")

# Async behavior test case (not applicable for this synchronous function)