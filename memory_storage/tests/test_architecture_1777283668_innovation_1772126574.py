import pytest

class MemoryStorage:
    def __init__(self):
        self.data = {}

    def save_data(self, key, value):
        try:
            if key is None or value is None:
                raise ValueError("Key and value cannot be None")
            self.data[key] = value
            print(f"Data saved successfully for key: {key}")
        except Exception as e:
            handle_error(e)

# Mock the handle_error function to avoid side effects in tests
def handle_error(e):
    pass

@pytest.fixture
def memory_storage():
    return MemoryStorage()

def test_happy_path(memory_storage):
    memory_storage.save_data("test_key", "test_value")
    assert memory_storage.data == {"test_key": "test_value"}

def test_edge_case_empty_key(memory_storage):
    result = memory_storage.save_data("", "test_value")
    assert result is None

def test_edge_case_none_key(memory_storage):
    with pytest.raises(ValueError) as exc_info:
        memory_storage.save_data(None, "test_value")
    assert str(exc_info.value) == "Key and value cannot be None"

def test_edge_case_empty_value(memory_storage):
    with pytest.raises(ValueError) as exc_info:
        memory_storage.save_data("test_key", "")
    assert str(exc_info.value) == "Key and value cannot be None"

def test_edge_case_none_value(memory_storage):
    with pytest.raises(ValueError) as exc_info:
        memory_storage.save_data("test_key", None)
    assert str(exc_info.value) == "Key and value cannot be None"