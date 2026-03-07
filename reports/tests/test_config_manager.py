import pytest

class MockDataSource:
    def load_config(self, config_name):
        if config_name == "valid_config":
            return {"key": "value"}
        elif config_name == "empty_config":
            return {}
        elif config_name is None:
            raise ValueError("Config name cannot be None")
        else:
            raise FileNotFoundError(f"Configuration {config_name} not found")

class ConfigManager:
    def __init__(self):
        self._configurations = {}

    def load_configuration(self, config_name, data_source):
        # Load configuration from a data source
        return data_source.load_config(config_name)

@pytest.fixture
def config_manager():
    return ConfigManager()

@pytest.fixture
def mock_data_source():
    return MockDataSource()

# Happy path (normal inputs)
def test_load_configuration_happy_path(config_manager, mock_data_source):
    result = config_manager.load_configuration("valid_config", mock_data_source)
    assert result == {"key": "value"}
    assert result in config_manager._configurations

# Edge cases
def test_load_configuration_empty_config(config_manager, mock_data_source):
    result = config_manager.load_configuration("empty_config", mock_data_source)
    assert result == {}
    assert result in config_manager._configurations

def test_load_configuration_none_config_name(config_manager, mock_data_source):
    with pytest.raises(ValueError) as exc_info:
        config_manager.load_configuration(None, mock_data_source)
    assert str(exc_info.value) == "Config name cannot be None"
    assert not config_manager._configurations

# Error cases
def test_load_configuration_file_not_found(config_manager, mock_data_source):
    with pytest.raises(FileNotFoundError) as exc_info:
        config_manager.load_configuration("nonexistent_config", mock_data_source)
    assert str(exc_info.value) == "Configuration nonexistent_config not found"
    assert not config_manager._configurations

# Async behavior
async def test_load_configuration_async(mock_data_source):
    import asyncio

    async def load_config_async(config_name):
        return mock_data_source.load_config(config_name)

    config_manager = ConfigManager()
    result = await config_manager.load_configuration("valid_config", MockDataSource())
    assert result == {"key": "value"}
    assert result in config_manager._configurations