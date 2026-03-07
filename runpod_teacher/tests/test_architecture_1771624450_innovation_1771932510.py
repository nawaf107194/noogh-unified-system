import pytest

def load_config(file_path):
    """Load configuration from a file."""
    with open(file_path, 'r') as config_file:
        return config_file.read()

@pytest.fixture
def sample_config_file(tmpdir):
    config_content = "sample_config"
    config_file = tmpdir.join("test_config.txt")
    config_file.write(config_content)
    return str(config_file)

def test_load_config_happy_path(sample_config_file):
    """Test load_config with a valid file path."""
    result = load_config(sample_config_file)
    assert result == "sample_config"

def test_load_config_empty_file(tmpdir):
    """Test load_config with an empty file."""
    empty_file = tmpdir.join("empty_config.txt")
    empty_file.write("")
    result = load_config(str(empty_file))
    assert result == ""

def test_load_config_nonexistent_file(tmpdir):
    """Test load_config with a non-existent file."""
    nonexistent_file = str(tmpdir.join("nonexistent_config.txt"))
    result = load_config(nonexistent_file)
    assert result is None

def test_load_config_null_input():
    """Test load_config with a None input."""
    result = load_config(None)
    assert result is None