import pytest

from shared.chunked_data_loader import ChunkedDataLoader

def test_happy_path():
    loader = ChunkedDataLoader("example.csv", chunk_size=1000, usecols=["col1", "col2"])
    assert loader.file_path == "example.csv"
    assert loader.chunk_size == 1000
    assert loader.usecols == ["col1", "col2"]
    assert loader.data_iterator is None

def test_empty_file_path():
    loader = ChunkedDataLoader("")
    assert loader.file_path == ""
    assert loader.chunk_size == 1000
    assert loader.usecols is None
    assert loader.data_iterator is None

def test_none_file_path():
    loader = ChunkedDataLoader(None)
    assert loader.file_path is None
    assert loader.chunk_size == 1000
    assert loader.usecols is None
    assert loader.data_iterator is None

def test_default_chunk_size():
    loader = ChunkedDataLoader("example.csv", usecols=["col1"])
    assert loader.file_path == "example.csv"
    assert loader.chunk_size == 1000
    assert loader.usecols == ["col1"]
    assert loader.data_iterator is None

def test_use_none_for_chunk_size():
    loader = ChunkedDataLoader("example.csv", chunk_size=None, usecols=["col1"])
    assert loader.file_path == "example.csv"
    assert loader.chunk_size is None
    assert loader.usecols == ["col1"]
    assert loader.data_iterator is None

def test_empty_usecols():
    loader = ChunkedDataLoader("example.csv", usecols=[])
    assert loader.file_path == "example.csv"
    assert loader.chunk_size == 1000
    assert loader.usecols == []
    assert loader.data_iterator is None

def test_none_usecols():
    loader = ChunkedDataLoader("example.csv", usecols=None)
    assert loader.file_path == "example.csv"
    assert loader.chunk_size == 1000
    assert loader.usecols is None
    assert loader.data_iterator is None

def test_invalid_file_path_type():
    with pytest.raises(TypeError):
        ChunkedDataLoader(123, chunk_size=1000, usecols=["col1"])

def test_invalid_chunk_size_type():
    with pytest.raises(TypeError):
        ChunkedDataLoader("example.csv", chunk_size="1000", usecols=["col1"])

def test_negative_chunk_size():
    loader = ChunkedDataLoader("example.csv", chunk_size=-1000, usecols=["col1"])
    assert loader.file_path == "example.csv"
    assert loader.chunk_size == 1000
    assert loader.usecols == ["col1"]
    assert loader.data_iterator is None

def test_large_chunk_size():
    loader = ChunkedDataLoader("example.csv", chunk_size=10**9, usecols=["col1"])
    assert loader.file_path == "example.csv"
    assert loader.chunk_size == 10**9
    assert loader.usecols == ["col1"]
    assert loader.data_iterator is None

def test_async_behavior():
    async def load_data(loader):
        async for chunk in loader:
            pass

    loader = ChunkedDataLoader("example.csv")
    pytest.mark.asyncio
    with pytest.raises(NotImplementedError):
        asyncio.run(load_data(loader))