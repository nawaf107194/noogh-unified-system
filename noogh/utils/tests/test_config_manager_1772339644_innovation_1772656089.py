import pytest

from noogh.utils import ConfigManager

def test_happy_path():
    # Test normal initialization
    config_manager = ConfigManager()
    assert isinstance(config_manager.configs, dict)
    assert len(config_manager.configs) == 0

def test_edge_cases():
    # Test multiple instances
    config_manager1 = ConfigManager()
    config_manager2 = ConfigManager()
    
    # Ensure each instance has its own configs
    assert config_manager1.configs is not config_manager2.configs
    
    # Test initial state
    assert isinstance(config_manager1.configs, dict)
    assert len(config_manager1.configs) == 0
    
    # Test type
    assert type(config_manager1.configs) == dict