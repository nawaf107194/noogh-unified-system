import pytest

from shared.feature_flag_manager import FeatureFlagManager

class TestFeatureFlagManager:

    @pytest.fixture
    def feature_flag_manager(self):
        # Initialize a FeatureFlagManager with some flags for testing
        manager = FeatureFlagManager()
        manager.flags = {
            'feature1': True,
            'feature2': False
        }
        return manager

    def test_happy_path(self, feature_flag_manager):
        # Happy path: Feature exists and is disabled successfully
        assert feature_flag_manager.disable_feature('feature1') is None
        assert feature_flag_manager.flags['feature1'] is False
        assert 'feature2' in feature_flag_manager.flags and feature_flag_manager.flags['feature2'] is False

    def test_edge_case_empty_string(self, feature_flag_manager):
        # Edge case: Empty string as feature_name
        with pytest.raises(KeyError) as exc_info:
            feature_flag_manager.disable_feature('')
        assert str(exc_info.value) == "Feature '' not found in configuration."

    def test_edge_case_none(self, feature_flag_manager):
        # Edge case: None as feature_name
        with pytest.raises(KeyError) as exc_info:
            feature_flag_manager.disable_feature(None)
        assert str(exc_info.value) == "Feature 'None' not found in configuration."

    def test_error_case_non_existent_feature(self, feature_flag_manager):
        # Error case: Feature does not exist
        with pytest.raises(KeyError) as exc_info:
            feature_flag_manager.disable_feature('feature3')
        assert str(exc_info.value) == "Feature 'feature3' not found in configuration."