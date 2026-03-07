import pytest

class ConfigManagementUtility:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config_data = self.load_config()

    def load_config(self):
        # Mock implementation for testing purposes
        if self.config_path:
            return {"key": "value"}
        else:
            return None

def test_happy_path():
    config_path = "/path/to/valid/config"
    utility = ConfigManagementUtility(config_path)
    assert utility.config_path == config_path
    assert utility.config_data == {"key": "value"}

def test_edge_case_empty_path():
    config_path = ""
    utility = ConfigManagementUtility(config_path)
    assert utility.config_path == config_path
    assert utility.config_data is None

def test_edge_case_none_path():
    config_path = None
    utility = ConfigManagementUtility(config_path)
    assert utility.config_path is None
    assert utility.config_data is None

# Note: There are no explicit error cases or async behavior in the provided code.