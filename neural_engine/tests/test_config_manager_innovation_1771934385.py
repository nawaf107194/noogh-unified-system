import pytest

class MockConfigManager:
    def __init__(self):
        self.config = {}

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values at once."""
        self.config.update(updates)

def test_update_config_happy_path():
    manager = MockConfigManager()
    manager.update_config({'key1': 'value1', 'key2': 42})
    assert manager.config == {'key1': 'value1', 'key2': 42}

def test_update_config_edge_case_empty_updates():
    manager = MockConfigManager()
    manager.update_config({})
    assert manager.config == {}

def test_update_config_edge_case_none_updates():
    manager = MockConfigManager()
    manager.update_config(None)
    assert manager.config == {}

def test_update_config_error_case_invalid_input_type():
    manager = MockConfigManager()
    with pytest.raises(TypeError):
        manager.update_config('not a dictionary')

def test_update_config_error_case_invalid_input_value():
    manager = MockConfigManager()
    with pytest.raises(TypeError):
        manager.update_config({'key': 123, 'invalid_value': None})