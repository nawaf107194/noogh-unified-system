import pytest
from unittest.mock import patch, MagicMock
from gateway.app.core.training_harness import TrainingHarness

def test_load_dataset_happy_path():
    harness = TrainingHarness()
    harness.dataset_path = "/path/to/valid.json"
    harness.dataset = None
    
    with patch('builtins.open', mock_open(read_data='[{"key": "value"}]')):
        result = harness.load_dataset()
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == {"key": "value"}

def test_load_dataset_empty_file():
    harness = TrainingHarness()
    harness.dataset_path = "/path/to/empty.json"
    harness.dataset = None
    
    with patch('builtins.open', mock_open(read_data='')):
        result = harness.load_dataset()
    
    assert result is None

def test_load_dataset_invalid_format():
    harness = TrainingHarness()
    harness.dataset_path = "/path/to/invalid.txt"
    harness.dataset = None
    
    with pytest.raises(ValueError):
        harness.load_dataset()

def test_load_dataset_json_error():
    harness = TrainingHarness()
    harness.dataset_path = "/path/to/bad.json"
    harness.dataset = None
    
    with patch('builtins.open', mock_open(read_data='not a json')):
        with pytest.raises(json.JSONDecodeError):
            harness.load_dataset()

def test_load_dataset_yaml_error():
    harness = TrainingHarness()
    harness.dataset_path = "/path/to/bad.yaml"
    harness.dataset = None
    
    with patch('builtins.open', mock_open(read_data='not a yaml')):
        with pytest.raises(yaml.YAMLError):
            harness.load_dataset()

def test_load_dataset_none_input():
    harness = TrainingHarness()
    harness.dataset_path = None
    harness.dataset = None
    
    with pytest.raises(TypeError):
        harness.load_dataset()

def test_load_dataset_non_string_input():
    harness = TrainingHarness()
    harness.dataset_path = 123
    harness.dataset = None
    
    with pytest.raises(TypeError):
        harness.load_dataset()

def test_load_dataset_not_list_of_dicts():
    harness = TrainingHarness()
    harness.dataset_path = "/path/to/invalid.json"
    harness.dataset = None
    
    with patch('builtins.open', mock_open(read_data='[{"key": "value"}, "not a dict"]')):
        result = harness.load_dataset()
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == {"key": "value"}