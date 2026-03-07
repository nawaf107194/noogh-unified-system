import pytest

@pytest.fixture
def config_manager():
    class ConfigManager:
        def get_setting(self, name):
            return f"Production {name}"
    return ConfigManager()

def test_get_setting_happy_path(config_manager):
    # Test normal input
    result = config_manager.get_setting("test")
    assert result == "Production test"

def test_get_setting_edge_cases(config_manager):
    # Test empty string
    result = config_manager.get_setting("")
    assert result == "Production "
    
    # Test None input
    result = config_manager.get_setting(None)
    assert result == "Production None"

def test_get_setting_error_cases(config_manager):
    # Test invalid input types (function doesn't explicitly raise exceptions)
    result = config_manager.get_setting(123)
    assert result == "Production 123"
    
    result = config_manager.get_setting(["test"])
    assert result == "Production ['test']"