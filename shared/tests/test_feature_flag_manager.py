import pytest
from unittest.mock import patch

class FeatureFlagManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.flags = self.load_flags()

    def load_flags(self):
        # Mocked version of load_flags for testing purposes
        return {"flag1": True, "flag2": False}

@pytest.fixture
def mock_load_flags():
    with patch.object(FeatureFlagManager, 'load_flags', return_value={"flag1": True, "flag2": False}):
        yield

def test_init_happy_path(mock_load_flags):
    manager = FeatureFlagManager("/path/to/config")
    assert manager.config_path == "/path/to/config"
    assert manager.flags == {"flag1": True, "flag2": False}

def test_init_empty_string(mock_load_flags):
    manager = FeatureFlagManager("")
    assert manager.config_path == ""
    assert manager.flags == {"flag1": True, "flag2": False}

def test_init_none_input():
    with pytest.raises(TypeError):
        FeatureFlagManager(None)

def test_init_invalid_input(mock_load_flags):
    with pytest.raises(Exception) as exc_info:
        FeatureFlagManager(12345)  # Passing an integer instead of a string
    assert "argument of type 'int' is not iterable" in str(exc_info.value)

# Since the function does not have any async behavior, we skip the async test.