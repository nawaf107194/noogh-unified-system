import pytest
from noogh_unified_system.src.shared.chunked_data_loader import ChunkedDataLoader

def test_happy_path():
    loader = ChunkedDataLoader('large_dataset.csv', chunk_size=5000, usecols=['col1', 'col2'])
    mock_print = lambda x: None  # Mock print function
    loader.process_chunk(mock_print)
    assert True  # Assuming process_chunk does not return anything meaningful

def test_empty_file():
    with pytest.raises(FileNotFoundError):
        ChunkedDataLoader('', chunk_size=5000, usecols=['col1', 'col2'])

def test_none_filename():
    with pytest.raises(ValueError):
        ChunkedDataLoader(None, chunk_size=5000, usecols=['col1', 'col2'])

def test_negative_chunk_size():
    with pytest.raises(ValueError):
        ChunkedDataLoader('large_dataset.csv', chunk_size=-1, usecols=['col1', 'col2'])

def test_invalid_usecols():
    with pytest.raises(KeyError):
        ChunkedDataLoader('large_dataset.csv', chunk_size=5000, usecols=['nonexistent_col'])