import pytest
import pandas as pd

from shared.data_aggregator import DataAggregator

# Happy path (normal inputs)
def test_load_csv_happy_path():
    aggregator = DataAggregator()
    data = "path/to/your/test.csv"
    result = aggregator._load_csv(data)
    assert isinstance(result, list)
    assert all(isinstance(item, dict) for item in result)

# Edge cases (empty, None, boundaries)
def test_load_csv_edge_cases():
    aggregator = DataAggregator()
    
    # Test with an empty file
    empty_data = "path/to/your/test_empty.csv"
    pd.DataFrame().to_csv(empty_data, index=False)
    result = aggregator._load_csv(empty_data)
    assert len(result) == 0
    
    # Test with None
    with pytest.raises(ValueError):
        aggregator._load_csv(None)

# Error cases (invalid inputs) ONLY IF the code explicitly raises them
def test_load_csv_error_cases():
    aggregator = DataAggregator()
    
    # Test with an invalid file path
    invalid_data = "path/to/your/test_invalid.csv"
    with pytest.raises(FileNotFoundError):
        aggregator._load_csv(invalid_data)

# Async behavior (if applicable)
# Note: This function does not contain any async behavior, so no specific test for it is needed.