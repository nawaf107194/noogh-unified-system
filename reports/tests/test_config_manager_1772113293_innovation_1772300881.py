import pytest

class ConfigManager:
    _instance = None
    _config_data: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._config_data = {}
        return cls._instance

def test_config_manager_happy_path():
    instance1 = ConfigManager()
    instance2 = ConfigManager()

    assert instance1 is instance2
    assert isinstance(instance1._config_data, dict)

def test_config_manager_edge_cases():
    # Edge cases are not applicable for this function as it does not accept any parameters.
    pass

def test_config_manager_error_cases():
    # There are no error cases in this function as it does not raise any exceptions.
    pass

async def test_config_manager_async_behavior():
    # Since the __new__ method is synchronous, there is no async behavior to test.
    pass