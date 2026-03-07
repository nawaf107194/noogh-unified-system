import pytest

from shared.chunked_data_loader import ChunkedDataLoader

def test_example_usage_happy_path(mocker):
    # Mock the process_chunk method to capture output
    mock_print = mocker.mock_print()
    
    # Create an instance of ChunkedDataLoader with normal inputs
    loader = ChunkedDataLoader('large_dataset.csv', chunk_size=5000, usecols=['col1', 'col2'])
    
    # Call the example_usage function
    example_usage()
    
    # Check if process_chunk was called with the correct arguments
    assert mock_print.call_count == 4  # Assuming 4 chunks for simplicity

def test_example_usage_edge_case_empty_filename():
    # Create an instance of ChunkedDataLoader with an empty filename
    loader = ChunkedDataLoader('', chunk_size=5000, usecols=['col1', 'col2'])
    
    # Call the example_usage function
    example_usage()
    
    # Check if process_chunk was not called
    assert not loader.process_chunk.called

def test_example_usage_edge_case_none_filename():
    # Create an instance of ChunkedDataLoader with None as filename
    loader = ChunkedDataLoader(None, chunk_size=5000, usecols=['col1', 'col2'])
    
    # Call the example_usage function
    example_usage()
    
    # Check if process_chunk was not called
    assert not loader.process_chunk.called

def test_example_usage_edge_case_boundary_chunk_size():
    # Create an instance of ChunkedDataLoader with boundary chunk size
    loader = ChunkedDataLoader('large_dataset.csv', chunk_size=1, usecols=['col1', 'col2'])
    
    # Call the example_usage function
    example_usage()
    
    # Check if process_chunk was called as many times as there are rows in the dataset

def test_example_usage_error_case_invalid_columns():
    with pytest.raises(ValueError):
        # Create an instance of ChunkedDataLoader with invalid columns
        loader = ChunkedDataLoader('large_dataset.csv', chunk_size=5000, usecols=['col3', 'col4'])
        
        # Call the example_usage function
        example_usage()

def test_example_usage_error_case_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        # Create an instance of ChunkedDataLoader with a nonexistent file
        loader = ChunkedDataLoader('nonexistent_dataset.csv', chunk_size=5000, usecols=['col1', 'col2'])
        
        # Call the example_usage function
        example_usage()