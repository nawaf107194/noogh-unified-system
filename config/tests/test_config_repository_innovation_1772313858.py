import pytest

class MockConfigManager:
    def update_config(self, new_config):
        # Simulate updating config
        self.config = new_config

def test_update_config_happy_path():
    mock_manager = MockConfigManager()
    config_repo = ConfigRepository(config_manager=mock_manager)
    new_config = {'key': 'value'}
    
    result = config_repo.update_config(new_config)
    
    assert mock_manager.config == new_config
    assert result is None  # Assuming update_config doesn't return anything

def test_update_config_none():
    mock_manager = MockConfigManager()
    config_repo = ConfigRepository(config_manager=mock_manager)
    new_config = None
    
    result = config_repo.update_config(new_config)
    
    assert mock_manager.config is None
    assert result is None

def test_update_config_empty_dict():
    mock_manager = MockConfigManager()
    config_repo = ConfigRepository(config_manager=mock_manager)
    new_config = {}
    
    result = config_repo.update_config(new_config)
    
    assert mock_manager.config == {}
    assert result is None

# Assuming there are no error cases or async behavior for this function