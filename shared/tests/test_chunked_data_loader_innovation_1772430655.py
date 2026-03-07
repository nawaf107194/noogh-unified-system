import pytest

from shared.chunked_data_loader import ChunkedDataLoader

def test_happy_path():
    loader = ChunkedDataLoader('path/to/file.csv', chunk_size=1000, usecols=['col1', 'col2'])
    assert loader.file_path == 'path/to/file.csv'
    assert loader.chunk_size == 1000
    assert loader.usecols == ['col1', 'col2']
    assert loader.data_iterator is None

def test_empty_file_path():
    loader = ChunkedDataLoader('')
    assert loader.file_path == ''
    assert loader.chunk_size == 1000
    assert loader.usecols is None
    assert loader.data_iterator is None

def test_none_file_path():
    loader = ChunkedDataLoader(None)
    assert loader.file_path is None
    assert loader.chunk_size == 1000
    assert loader.usecols is None
    assert loader.data_iterator is None

def test_boundary_chunk_size_zero():
    loader = ChunkedDataLoader('path/to/file.csv', chunk_size=0)
    assert loader.file_path == 'path/to/file.csv'
    assert loader.chunk_size == 1000
    assert loader.usecols is None
    assert loader.data_iterator is None

def test_boundary_chunk_size_negative():
    loader = ChunkedDataLoader('path/to/file.csv', chunk_size=-5)
    assert loader.file_path == 'path/to/file.csv'
    assert loader.chunk_size == 1000
    assert loader.usecols is None
    assert loader.data_iterator is None

def test_none_usecols():
    loader = ChunkedDataLoader('path/to/file.csv', usecols=None)
    assert loader.file_path == 'path/to/file.csv'
    assert loader.chunk_size == 1000
    assert loader.usecols is None
    assert loader.data_iterator is None

def test_empty_usecols():
    loader = ChunkedDataLoader('path/to/file.csv', usecols='')
    assert loader.file_path == 'path/to/file.csv'
    assert loader.chunk_size == 1000
    assert loader.usecols == []
    assert loader.data_iterator is None