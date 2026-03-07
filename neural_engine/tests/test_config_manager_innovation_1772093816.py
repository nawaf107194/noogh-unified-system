import pytest

class MockConfigManager:
    def __init__(self):
        self.config = {}

    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value by key."""
        self.config[key] = value

@pytest.fixture
def config_manager():
    return MockConfigManager()

def test_set_config_happy_path(config_manager):
    # Test normal inputs
    key = "test_key"
    value = "test_value"
    config_manager.set_config(key, value)
    assert config_manager.config == {key: value}

def test_set_config_edge_case_empty_key(config_manager):
    # Test with empty key
    key = ""
    value = "test_value"
    config_manager.set_config(key, value)
    assert config_manager.config == {}

def test_set_config_edge_case_none_key(config_manager):
    # Test with None key
    key = None
    value = "test_value"
    config_manager.set_config(key, value)
    assert config_manager.config == {None: value}

def test_set_config_edge_case_empty_value(config_manager):
    # Test with empty value
    key = "test_key"
    value = ""
    config_manager.set_config(key, value)
    assert config_manager.config == {key: ""}

def test_set_config_edge_case_none_value(config_manager):
    # Test with None value
    key = "test_key"
    value = None
    config_manager.set_config(key, value)
    assert config_manager.config == {key: None}