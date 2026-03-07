import pytest

class ConfigManager:
    def get_setting(self, name):
        return f"Production {name}"

@pytest.fixture
def config_manager():
    return ConfigManager()

def test_get_setting_happy_path(config_manager):
    assert config_manager.get_setting("feature") == "Production feature"

def test_get_setting_empty_input(config_manager):
    assert config_manager.get_setting("") == "Production "

def test_get_setting_none_input(config_manager):
    assert config_manager.get_setting(None) is None

def test_get_setting_boundary_input(config_manager):
    assert config_manager.get_setting("boundary") == "Production boundary"

# Error cases are not applicable as the function does not raise any exceptions