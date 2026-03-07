import pytest

from shared.feature_flag_manager import FeatureFlagManager

def test_feature_flag_manager_happy_path():
    # Happy path: normal inputs
    config_path = "/path/to/config.json"
    feature_flag_manager = FeatureFlagManager(config_path)
    assert feature_flag_manager.config_path == config_path
    assert isinstance(feature_flag_manager.flags, dict)

def test_feature_flag_manager_edge_case_empty_config_path():
    # Edge case: empty config path
    with pytest.raises(ValueError):
        FeatureFlagManager("")

def test_feature_flag_manager_edge_case_none_config_path():
    # Edge case: None config path
    with pytest.raises(ValueError):
        FeatureFlagManager(None)

def test_feature_flag_manager_error_case_invalid_config_path():
    # Error case: invalid config path (non-existent file)
    import os
    non_existent_path = "/path/to/nonexistent/file.json"
    if not os.path.exists(non_existent_path):
        with pytest.raises(FileNotFoundError):
            FeatureFlagManager(non_existent_path)

def test_feature_flag_manager_edge_case_invalid_config_format():
    # Edge case: invalid config format (not a JSON file)
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"This is not valid JSON")
        temp_file_name = temp_file.name
        with pytest.raises(ValueError):
            FeatureFlagManager(temp_file_name)