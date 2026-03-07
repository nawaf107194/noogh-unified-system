import pytest

from noogh.utils.config_manager_1771943049 import ConfigManager

class TestConfigManager:

    @pytest.fixture
    def config_manager(self):
        return ConfigManager.get_instance()

    def test_load_config_happy_path(self, config_manager):
        # Arrange
        expected_data = {"key": "value"}
        
        # Mock the actual loading logic to return expected data
        with patch.object(ConfigManager, 'load_config_file', return_value=expected_data):
            # Act
            result = config_manager.load_config()
            
            # Assert
            assert result == expected_data
            assert config_manager.config_data == expected_data

    def test_load_config_edge_cases(self, config_manager):
        # Arrange
        with patch.object(ConfigManager, 'load_config_file', side_effect=[None, {}, {"key": None}]):
            
            # Act & Assert
            result1 = config_manager.load_config()
            assert result1 is None
            assert config_manager.config_data is None

            result2 = config_manager.load_config()
            assert result2 == {}
            assert config_manager.config_data == {}

            result3 = config_manager.load_config()
            assert result3 == {"key": None}
            assert config_manager.config_data == {"key": None}

    def test_load_config_error_cases(self, config_manager):
        # Arrange
        with patch.object(ConfigManager, 'load_config_file', side_effect=IOError):
            
            # Act & Assert
            result = config_manager.load_config()
            assert result is None
            assert config_manager.config_data is None

    @pytest.mark.asyncio
    async def test_load_config_async(self, config_manager):
        # Arrange
        expected_data = {"key": "value"}
        
        # Mock the actual loading logic to return expected data asynchronously
        with patch.object(ConfigManager, 'load_config_file_async', return_value=expected_data):
            # Act
            result = await config_manager.load_config_async()
            
            # Assert
            assert result == expected_data
            assert config_manager.config_data == expected_data