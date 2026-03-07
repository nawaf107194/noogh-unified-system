import pytest

from unified_core.core.config_manager import ConfigManager

class TestConfigManager:

    @pytest.fixture
    def config_manager(self):
        return ConfigManager()

    def test_set_config_happy_path(self, config_manager):
        key = "test_key"
        value = 42
        config_manager.set_config(key, value)
        assert config_manager.config[key] == value

    def test_set_config_empty_key(self, config_manager):
        key = ""
        value = "empty_value"
        config_manager.set_config(key, value)
        assert config_manager.config[key] == value

    def test_set_config_none_value(self, config_manager):
        key = "none_value_key"
        value = None
        config_manager.set_config(key, value)
        assert config_manager.config[key] is None

    def test_set_config_boundary_key_length(self, config_manager):
        key = "a" * 1024  # Assuming the max length for keys is 1024
        value = "boundary_value"
        config_manager.set_config(key, value)
        assert config_manager.config[key] == value

    def test_set_config_boundary_value_length(self, config_manager):
        key = "boundary_key"
        value = "a" * 1024  # Assuming the max length for values is 1024
        config_manager.set_config(key, value)
        assert config_manager.config[key] == value

    def test_set_config_invalid_input_type(self, config_manager):
        key = "invalid_key"
        value = {"not": "valid"}
        with pytest.raises(TypeError):
            config_manager.set_config(key, value)