import pytest
from shared.data_aggregator import DataAggregator
import pandas as pd
import os

@pytest.fixture
def data_aggregator():
    return DataAggregator()

def test_load_csv_happy_path(data_aggregator, tmpdir):
    # Create a temporary CSV file with some data
    csv_file = tmpdir.join("data.csv")
    csv_file.write("""id,name,value\n1,Alice,10\n2,Bob,20""")
    
    result = data_aggregator._load_csv(csv_file.strpath)
    expected = [{'id': '1', 'name': 'Alice', 'value': '10'}, {'id': '2', 'name': 'Bob', 'value': '20'}]
    assert result == expected

def test_load_csv_empty_file(data_aggregator, tmpdir):
    # Create a temporary empty CSV file
    csv_file = tmpdir.join("data.csv")
    csv_file.write("")
    
    result = data_aggregator._load_csv(csv_file.strpath)
    assert result == []

def test_load_csv_none_input(data_aggregator):
    # Test with None input
    result = data_aggregator._load_csv(None)
    assert result is None

def test_load_csv_invalid_path(data_aggregator, tmpdir):
    # Test with an invalid file path
    csv_file = tmpdir.join("nonexistent.csv")
    
    result = data_aggregator._load_csv(csv_file.strpath)
    assert result is None