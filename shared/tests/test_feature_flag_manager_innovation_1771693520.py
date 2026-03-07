import pytest

from shared.feature_flag_manager import FeatureFlagManager, Flag

class MockFeatureFlagManager(FeatureFlagManager):
    def __init__(self):
        self.flags = {
            "feature1": Flag(True),
            "feature2": Flag(False)
        }

def test_list_features_happy_path():
    manager = MockFeatureFlagManager()
    result = manager.list_features()
    assert isinstance(result, list)
    assert len(result) == 2
    assert "feature1" in result
    assert "feature2" in result

def test_list_features_empty_flags():
    manager = FeatureFlagManager()
    result = manager.list_features()
    assert isinstance(result, list)
    assert len(result) == 0

def test_list_features_none_flags():
    manager = MockFeatureFlagManager()
    manager.flags = None
    result = manager.list_features()
    assert isinstance(result, list)
    assert len(result) == 0

def test_list_features_boundary_case():
    manager = FeatureFlagManager()
    for _ in range(100):
        manager.flags["feature_" + str(_)] = Flag(True if _ % 2 == 0 else False)
    result = manager.list_features()
    assert isinstance(result, list)
    assert len(result) == 100
    assert all(feature.startswith("feature_") for feature in result)

def test_list_features_async_behavior():
    # Since the function is synchronous and doesn't involve any async behavior,
    # there's no need to test it as async. However, if the function were async,
    # you would use an event loop to run the async function and assert its output.
    pass