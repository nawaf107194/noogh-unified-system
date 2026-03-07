import pytest

class TestConfigManager:

    @pytest.fixture
    def config_manager(self):
        from noogh.utils.config_manager_1772358549 import ConfigManager
        return ConfigManager()

    def test_load_config_happy_path(self, config_manager, monkeypatch):
        # Arrange
        mock_config = {"key": "value"}
        config_source = MockConfigSource(mock_config)
        config_manager.config_source = config_source

        # Act
        result = config_manager.load_config()

        # Assert
        assert result == mock_config

    def test_load_config_edge_case_none(self, config_manager, monkeypatch):
        # Arrange
        mock_config = None
        config_source = MockConfigSource(mock_config)
        config_manager.config_source = config_source

        # Act
        result = config_manager.load_config()

        # Assert
        assert result is None

    def test_load_config_edge_case_empty(self, config_manager, monkeypatch):
        # Arrange
        mock_config = {}
        config_source = MockConfigSource(mock_config)
        config_manager.config_source = config_source

        # Act
        result = config_manager.load_config()

        # Assert
        assert result == {}

    def test_load_config_error_case_invalid_input(self, config_manager, monkeypatch):
        # Arrange
        class InvalidConfigSource:
            def load(self):
                raise ValueError("Invalid input")

        config_source = InvalidConfigSource()
        config_manager.config_source = config_source

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid input"):
            config_manager.load_config()

class MockConfigSource:
    def __init__(self, config):
        self.config = config

    def load(self):
        return self.config