import pytest

def test_load_config_with_valid_file(tmp_path):
    """Test loading config from a valid file with content."""
    test_content = "test_config_content"
    config_file = tmp_path / "test_config.txt"
    config_file.write_text(test_content)
    
    result = load_config(config_file)
    assert result == test_content

def test_load_config_with_empty_file(tmp_path):
    """Test loading config from an empty file."""
    config_file = tmp_path / "empty_config.txt"
    config_file.write_text("")
    
    result = load_config(config_file)
    assert result == ""

def test_load_config_with_none_path():
    """Test loading config with None file path."""
    result = load_config(None)
    assert result is None

def test_load_config_with_nonexistent_file(tmp_path):
    """Test loading config from a non-existent file."""
    nonexistent_file = tmp_path / "nonexistent.txt"
    result = load_config(nonexistent_file)
    assert result is None

def test_load_config_with_invalid_path():
    """Test loading config with an invalid file path."""
    invalid_path = "/nonexistent_directory/config.txt"
    result = load_config(invalid_path)
    assert result is None