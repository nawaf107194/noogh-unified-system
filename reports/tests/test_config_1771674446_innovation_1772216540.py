import pytest

class ConfigManager:
    def __init__(self):
        self._configurations = {
            'default': {'key': 'value'}
        }

    def get_configuration(self, name):
        return self._configurations.get(name)

@pytest.fixture
def config_manager():
    return ConfigManager()

def test_get_configuration_happy_path(config_manager):
    assert config_manager.get_configuration('default') == {'key': 'value'}

def test_get_configuration_non_existent_key(config_manager):
    assert config_manager.get_configuration('nonexistent') is None

def test_get_configuration_empty_input(config_manager):
    assert config_manager.get_configuration(None) is None
    assert config_manager.get_configuration('') is None

def test_get_configuration_boundary_case(config_manager):
    # Assuming 'default' is a valid configuration name and there are no boundary cases to consider
    pass  # No specific actions needed for this example

# If the function were async, you might have tests like:
# @pytest.mark.asyncio
# async def test_async_get_configuration_happy_path(config_manager):
#     assert await config_manager.get_configuration('default') == {'key': 'value'}