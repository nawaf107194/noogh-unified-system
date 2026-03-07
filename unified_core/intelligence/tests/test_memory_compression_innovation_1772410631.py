import pytest
from unified_core.intelligence.memory_compression import MemoryCompression

@pytest.fixture
def memory_compression():
    return MemoryCompression()

def test_compress_entry_happy_path(memory_compression):
    entry = {
        "content": "This is a sample content for testing the compress_entry function."
    }
    result = memory_compression.compress_entry(entry)
    assert result == {
        "compressed_data": {
            "summary": "This is a sample content for testing the compress_entry f...",
            "details_hash": hash("This is a sample content for testing the compress_entry function.")
        }
    }

def test_compress_entry_empty_content(memory_compression):
    entry = {
        "content": ""
    }
    result = memory_compression.compress_entry(entry)
    assert result == {
        "compressed_data": {
            "summary": "",
            "details_hash": hash("")
        }
    }

def test_compress_entry_none_content(memory_compression):
    entry = {
        "content": None
    }
    result = memory_compression.compress_entry(entry)
    assert result == {
        "compressed_data": {
            "summary": "None",
            "details_hash": hash(None)
        }
    }

def test_compress_entry_boundary_content(memory_compression):
    content = "a" * 105  # Exceeds the summary length of 100
    entry = {
        "content": content
    }
    result = memory_compression.compress_entry(entry)
    assert result == {
        "compressed_data": {
            "summary": content[:100],
            "details_hash": hash(content)
        }
    }

def test_compress_entry_invalid_input_no_content(memory_compression):
    entry = {}
    result = memory_compression.compress_entry(entry)
    assert result == {
        "compressed_data": {
            "summary": "",
            "details_hash": hash("")
        }
    }

def test_compress_entry_invalid_input_missing_content_key(memory_compression):
    entry = {"other_key": "value"}
    result = memory_compression.compress_entry(entry)
    assert result == {
        "compressed_data": {
            "summary": "",
            "details_hash": hash("")
        }
    }