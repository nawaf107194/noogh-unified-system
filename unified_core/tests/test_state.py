import pytest

class MockState:
    def __init__(self):
        self._data = {
            "key1": "value1",
            "key2": 42,
            None: "NoneValue"
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get current value for a key."""
        return self._data.get(key, default)

@pytest.fixture
def state():
    return MockState()

def test_get_happy_path(state):
    assert state.get("key1") == "value1"
    assert state.get("key2") == 42

def test_get_empty_key(state):
    assert state.get("") is None

def test_get_none_key(state):
    assert state.get(None) == "NoneValue"

def test_get_non_existent_key_with_default(state):
    assert state.get("nonexistent", "default_value") == "default_value"

def test_get_non_existent_key_without_default(state):
    assert state.get("nonexistent") is None