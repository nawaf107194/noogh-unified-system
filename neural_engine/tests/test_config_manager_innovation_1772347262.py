import pytest

class MockConfigManager:
    def __init__(self):
        self.config = {}

    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value by key."""
        self.config[key] = value

# Tests for the set_config function

def test_set_config_happy_path():
    config_manager = MockConfigManager()
    config_manager.set_config('test_key', 'test_value')
    assert config_manager.config == {'test_key': 'test_value'}

def test_set_config_empty_key():
    config_manager = MockConfigManager()
    config_manager.set_config('', 'test_value')
    assert config_manager.config == {}

def test_set_config_none_key():
    config_manager = MockConfigManager()
    config_manager.set_config(None, 'test_value')
    assert config_manager.config is None

def test_set_config_boundary_values():
    config_manager = MockConfigManager()
    config_manager.set_config('boundary_key', 1234567890)
    assert config_manager.config == {'boundary_key': 1234567890}

# Error cases are not applicable as the function does not raise any exceptions