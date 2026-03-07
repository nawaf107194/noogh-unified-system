import pytest

from unified_core.system.memory_summarizer_1771983920 import MemorySummarizer

def test_init_happy_path():
    db_path = "/path/to/db"
    summarizer = MemorySummarizer(db_path)
    assert summarizer.db_path == db_path

def test_init_edge_case_empty_string():
    with pytest.raises(ValueError):
        MemorySummarizer("")

def test_init_edge_case_none():
    with pytest.raises(ValueError):
        MemorySummarizer(None)

def test_init_edge_case_boundary_long_string():
    # Assuming a reasonable boundary length for demonstration
    long_string = "a" * 10000
    summarizer = MemorySummarizer(long_string)
    assert summarizer.db_path == long_string

def test_init_error_case_invalid_input_type():
    with pytest.raises(ValueError):
        MemorySummarizer(12345)

def test_init_error_case_empty_dict():
    with pytest.raises(ValueError):
        MemorySummarizer({})