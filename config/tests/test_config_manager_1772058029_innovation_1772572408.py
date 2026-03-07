import pytest

class TestConfigManager:
    def setup_method(self):
        self.config_manager = ConfigManager()

    def test_get_setting_happy_path(self):
        result = self.config_manager.get_setting("value")
        assert result == "Production value"

    def test_get_setting_empty_string(self):
        result = self.config_manager.get_setting("")
        assert result == "Production "

    def test_get_setting_none_input(self):
        result = self.config_manager.get_setting(None)
        assert result == "Production None"