import pytest
from unified_core.intelligence.memory_compression import MemoryCompression

def test_compress_entry_happy_path():
    # Given
    memory_compression = MemoryCompression()
    entry = {
        "content": "This is a sample content that will be compressed."
    }
    
    # When
    result = memory_compression.compress_entry(entry)
    
    # Then
    assert "compressed_data" in result
    assert "summary" in result["compressed_data"]
    assert len(result["compressed_data"]["summary"]) == 100
    assert "details_hash" in result["compressed_data"]

def test_compress_entry_edge_case_empty_content():
    # Given
    memory_compression = MemoryCompression()
    entry = {
        "content": ""
    }
    
    # When
    result = memory_compression.compress_entry(entry)
    
    # Then
    assert "compressed_data" in result
    assert "summary" in result["compressed_data"]
    assert len(result["compressed_data"]["summary"]) == 0
    assert "details_hash" in result["compressed_data"]

def test_compress_entry_edge_case_none_content():
    # Given
    memory_compression = MemoryCompression()
    entry = {
        "content": None
    }
    
    # When
    result = memory_compression.compress_entry(entry)
    
    # Then
    assert "compressed_data" in result
    assert "summary" in result["compressed_data"]
    assert len(result["compressed_data"]["summary"]) == 0
    assert "details_hash" in result["compressed_data"]

def test_compress_entry_edge_case_boundary_content():
    # Given
    memory_compression = MemoryCompression()
    entry = {
        "content": "A" * 100
    }
    
    # When
    result = memory_compression.compress_entry(entry)
    
    # Then
    assert "compressed_data" in result
    assert "summary" in result["compressed_data"]
    assert len(result["compressed_data"]["summary"]) == 100
    assert "details_hash" in result["compressed_data"]

def test_compress_entry_error_case_invalid_input():
    # Given
    memory_compression = MemoryCompression()
    entry = {
        "content": []
    }
    
    # When
    result = memory_compression.compress_entry(entry)
    
    # Then
    assert result is None

def test_compress_entry_error_case_missing_key():
    # Given
    memory_compression = MemoryCompression()
    entry = {}
    
    # When
    result = memory_compression.compress_entry(entry)
    
    # Then
    assert result is None