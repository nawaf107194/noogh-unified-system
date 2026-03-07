import pytest
from unittest.mock import patch, mock_open
from unified_core.core.config_manager import ConfigManager

def test_load_config_happy_path():
    """Test loading a configuration file correctly."""
    config_path = '/path/to/config.json'
    expected_config = {
        'key': 'value',
        'another_key': 42
    }

    with patch('builtins.open', mock_open(read_data=json.dumps(expected_config))):
        cm = ConfigManager()
        cm.load_config(config_path)
    
    assert cm.config == expected_config

def test_load_config_empty_file():
    """Test loading an empty JSON file."""
    config_path = '/path/to/empty_config.json'
    
    with patch('builtins.open', mock_open(read_data='')):
        cm = ConfigManager()
        cm.load_config(config_path)
    
    assert cm.config == {}

def test_load_config_none_path():
    """Test loading with None path."""
    cm = ConfigManager()
    cm.load_config(None)
    
    assert cm.config is None

def test_load_config_invalid_json():
    """Test loading an invalid JSON file."""
    config_path = '/path/to/invalid_config.json'
    
    with patch('builtins.open', mock_open(read_data='{"key": "value",')):
        cm = ConfigManager()
        cm.load_config(config_path)
    
    assert cm.config is None

def test_load_config_nonexistent_file():
    """Test loading a non-existent file."""
    config_path = '/path/to/non_existent.json'
    
    with patch('builtins.open', side_effect=FileNotFoundError):
        cm = ConfigManager()
        cm.load_config(config_path)
    
    assert cm.config is None