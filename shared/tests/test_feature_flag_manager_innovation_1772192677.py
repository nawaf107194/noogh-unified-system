import pytest
from shared.feature_flag_manager import FeatureFlagManager

def test_load_flags_happy_path():
    manager = FeatureFlagManager("test_config.json")
    with open(manager.config_path, 'w') as file:
        json.dump({"feature1": True, "feature2": False}, file)
    
    flags = manager.load_flags()
    assert flags == {"feature1": True, "feature2": False}

def test_load_flags_empty_file():
    manager = FeatureFlagManager("empty_config.json")
    with open(manager.config_path, 'w') as file:
        pass
    
    flags = manager.load_flags()
    assert flags == {}

def test_load_flags_nonexistent_file():
    manager = FeatureFlagManager("non_existent_config.json")
    
    flags = manager.load_flags()
    assert flags == {}