import pytest

from unified_core.system.memory_compressor import MemoryCompressor

def test_happy_path():
    db_path = "/path/to/database"
    compressor = MemoryCompressor(db_path)
    assert isinstance(compressor, MemoryCompressor)
    assert compressor.db_path == db_path

def test_edge_case_empty_db_path():
    with pytest.raises(ValueError):
        compressor = MemoryCompressor("")

def test_edge_case_none_db_path():
    with pytest.raises(ValueError):
        compressor = MemoryCompressor(None)

def test_error_case_invalid_input_type():
    with pytest.raises(TypeError):
        compressor = MemoryCompressor(12345)