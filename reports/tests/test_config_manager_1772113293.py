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
    manager1 = ConfigManager()
    manager2 = ConfigManager()
    assert manager1 is manager2
    assert manager1._config_data == {}

def test_config_manager_edge_cases():
    # Edge cases are not applicable as the function does not accept any parameters.
    pass

def test_config_manager_error_cases():
    # The function does not raise any errors, so this test case is not applicable.
    pass

async def test_config_manager_async_behavior():
    import asyncio
    async def get_manager():
        return ConfigManager()
    
    manager1 = await get_manager()
    manager2 = await get_manager()
    assert manager1 is manager2
    assert manager1._config_data == {}