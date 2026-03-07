import pytest
import json
from pathlib import Path
from unittest.mock import patch

@pytest.fixture
def test_fabric(tmp_path):
    test_data = {"neurons": [{"id": 1, "connections": []}]}
    fabric_file = tmp_path / "fabric.json"
    with open(fabric_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f)
    return fabric_file

def test_load_fabric_happy_path(test_fabric):
    # Test loading valid fabric data
    with patch('src.prune_neurons.FABRIC_PATH', test_fabric):
        result = load_fabric()
    assert result == {"neurons": [{"id": 1, "connections": []}]}

def test_load_fabric_empty_file(tmp_path):
    # Test loading empty file
    fabric_file = tmp_path / "fabric.json"
    fabric_file.write_text('')
    with patch('src.prune_neurons.FABRIC_PATH', fabric_file):
        with pytest.raises(json.JSONDecodeError):
            load_fabric()

def test_load_fabric_file_not_found(tmp_path):
    # Test when fabric file doesn't exist
    non_existent_file = tmp_path / "nonexistent.json"
    with patch('src.prune_neurons.FABRIC_PATH', non_existent_file):
        with pytest.raises(FileNotFoundError):
            load_fabric()

def test_load_fabric_invalid_json(tmp_path):
    # Test loading file with invalid JSON
    invalid_json_file = tmp_path / "invalid.json"
    invalid_json_file.write_text("invalid json")
    with patch('src.prune_neurons.FABRIC_PATH', invalid_json_file):
        with pytest.raises(json.JSONDecodeError):
            load_fabric()