import pytest
from pathlib import Path
import json

from gateway.app.api.evolution_api import _read_fragile_files, MEMORY_DIR

@pytest.fixture
def sample_json_file(tmp_path):
    sample_data = {"file1": 0.5, "file2": 0.8}
    json_file = tmp_path / "fragile_files.json"
    json_file.write_text(json.dumps(sample_data))
    return str(json_file)

def test_happy_path(sample_json_file):
    """Test normal inputs."""
    result = _read_fragile_files()
    assert isinstance(result, dict)
    assert result == {"file1": 0.5, "file2": 0.8}

def test_empty_file(tmp_path):
    """Test with an empty file."""
    json_file = tmp_path / "fragile_files.json"
    json_file.write_text("{}")
    result = _read_fragile_files()
    assert isinstance(result, dict)
    assert result == {}

def test_missing_file(tmp_path):
    """Test with a non-existent file."""
    non_existent_file = Path(tmp_path) / "non_existent.json"
    result = _read_fragile_files()
    assert isinstance(result, dict)
    assert result == {}

def test_invalid_json(tmp_path):
    """Test with an invalid JSON file."""
    json_file = tmp_path / "fragile_files.json"
    json_file.write_text("invalid json")
    result = _read_fragile_files()
    assert isinstance(result, dict)
    assert result == {}