import pytest

class MockMemoryStorage:
    def __init__(self):
        self.models = {}

    def load_model(self, model_name):
        with self.engine.connect() as connection:
            result = connection.execute("SELECT * FROM models WHERE name = :model_name", {'model_name': model_name}).fetchone()
            return result

class MockEngine:
    def connect(self):
        return MockConnection()

class MockConnection:
    def execute(self, query, params):
        if 'name' in params and params['name'] == "valid_model":
            return [{'id': 1, 'name': 'valid_model', 'data': '{"key": "value"}'}]
        elif not params.get('name'):
            return None
        else:
            raise ValueError("Model not found")

@pytest.fixture
def memory_storage():
    instance = MockMemoryStorage()
    instance.engine = MockEngine()
    return instance

def test_load_model_happy_path(memory_storage):
    result = memory_storage.load_model("valid_model")
    assert result == {'id': 1, 'name': 'valid_model', 'data': '{"key": "value"}'}

def test_load_model_empty_input(memory_storage):
    result = memory_storage.load_model("")
    assert result is None

def test_load_model_none_input(memory_storage):
    result = memory_storage.load_model(None)
    assert result is None

def test_load_model_boundary_condition(memory_storage):
    # Assuming boundary condition means a very long string
    long_string = "a" * 10000
    result = memory_storage.load_model(long_string)
    assert result == {'id': 1, 'name': 'valid_model', 'data': '{"key": "value"}'}

def test_load_model_invalid_input(memory_storage):
    with pytest.raises(ValueError) as exc_info:
        memory_storage.load_model("invalid_model")
    assert str(exc_info.value) == "Model not found"