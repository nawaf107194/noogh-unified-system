import pytest

from unified_core.intelligence.memory_compression import MemoryCompressor, compress_entry

def test_compress_entry_happy_path():
    compressor = MemoryCompressor()
    entry = {
        "content": "This is a sample memory entry that needs to be compressed."
    }
    result = compressor.compress_entry(entry)
    assert isinstance(result, dict)
    assert "compressed_data" in result
    assert "summary" in result["compressed_data"]
    assert "details_hash" in result["compressed_data"]
    assert len(result["compressed_data"]["summary"]) <= 100

def test_compress_entry_empty_content():
    compressor = MemoryCompressor()
    entry = {
        "content": ""
    }
    result = compressor.compress_entry(entry)
    assert isinstance(result, dict)
    assert "compressed_data" in result
    assert "summary" in result["compressed_data"]
    assert result["compressed_data"]["summary"] == ""
    assert "details_hash" in result["compressed_data"]

def test_compress_entry_none_content():
    compressor = MemoryCompressor()
    entry = {
        "content": None
    }
    result = compressor.compress_entry(entry)
    assert isinstance(result, dict)
    assert "compressed_data" in result
    assert "summary" in result["compressed_data"]
    assert result["compressed_data"]["summary"] is None
    assert "details_hash" in result["compressed_data"]

def test_compress_entry_boundary_content():
    compressor = MemoryCompressor()
    entry = {
        "content": "a" * 100
    }
    result = compressor.compress_entry(entry)
    assert isinstance(result, dict)
    assert "compressed_data" in result
    assert "summary" in result["compressed_data"]
    assert len(result["compressed_data"]["summary"]) == 100
    assert "details_hash" in result["compressed_data"]

def test_compress_entry_invalid_input():
    compressor = MemoryCompressor()
    entry = {
        "content": {}
    }
    with pytest.raises(TypeError):
        compressor.compress_entry(entry)