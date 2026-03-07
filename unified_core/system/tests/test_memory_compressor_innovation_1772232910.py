import pytest

class MockMemoryCompressor:
    def __init__(self, db_path):
        self.db_path = db_path

@pytest.fixture
def memory_compressor():
    return MockMemoryCompressor

def test_happy_path(memory_compressor):
    compressor = memory_compressor("/path/to/db")
    assert compressor.db_path == "/path/to/db"

def test_edge_case_empty_string(memory_compressor):
    with pytest.raises(ValueError):
        memory_compressor("")

def test_edge_case_none(memory_compressor):
    with pytest.raises(TypeError):
        memory_compressor(None)

def test_edge_case_boundary_string(memory_compressor):
    compressor = memory_compressor("/")
    assert compressor.db_path == "/"

def test_error_case_invalid_input(memory_compressor):
    with pytest.raises(TypeError):
        memory_compressor(12345)