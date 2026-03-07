import pytest

from runpod_teacher.architecture_factory import ArchitectureFactory

class MockArchitecture:
    def __init__(self, *args, **kwargs):
        pass

@pytest.fixture
def factory():
    factory_instance = ArchitectureFactory()
    factory_instance._architectures = {
        'mock_key': MockArchitecture
    }
    return factory_instance

def test_happy_path(factory):
    result = factory.create_architecture('mock_key')
    assert isinstance(result, MockArchitecture)

def test_edge_case_empty_key(factory):
    with pytest.raises(ValueError) as exc_info:
        factory.create_architecture('')
    assert str(exc_info.value) == "No architecture found with key ''."

def test_edge_case_none_key(factory):
    with pytest.raises(ValueError) as exc_info:
        factory.create_architecture(None)
    assert str(exc_info.value) == "No architecture found with key 'None'."

def test_error_case_invalid_key(factory):
    result = factory.create_architecture('nonexistent_key')
    assert result is None