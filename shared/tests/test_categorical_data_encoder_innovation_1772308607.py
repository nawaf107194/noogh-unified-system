import pytest
import pandas as pd
from shared.categorical_data_encoder import CategoricalDataEncoder

def test_one_hot_encode_happy_path():
    # Create a sample DataFrame with categorical columns
    data = {
        'color': ['red', 'blue', 'green'],
        'size': ['S', 'M', 'L']
    }
    df = pd.DataFrame(data)
    
    # Initialize the encoder and perform one-hot encoding
    encoder = CategoricalDataEncoder(df)
    encoded_df = encoder.one_hot_encode(['color', 'size'])
    
    # Expected output columns
    expected_columns = ['color_red', 'color_blue', 'color_green', 'size_S', 'size_M', 'size_L']
    
    # Assert the shape of the DataFrame
    assert encoded_df.shape == (3, 6)
    
    # Assert the presence of the expected columns
    assert all(col in encoded_df.columns for col in expected_columns)
    
    # Assert that the original columns are dropped
    assert not any(col in encoded_df.columns for col in ['color', 'size'])

def test_one_hot_encode_none_columns():
    # Create a sample DataFrame with categorical columns
    data = {
        'color': ['red', 'blue', 'green'],
        'size': ['S', 'M', 'L']
    }
    df = pd.DataFrame(data)
    
    # Initialize the encoder and perform one-hot encoding on all categorical columns
    encoder = CategoricalDataEncoder(df)
    encoded_df = encoder.one_hot_encode()
    
    # Expected output columns
    expected_columns = ['color_red', 'color_blue', 'color_green', 'size_S', 'size_M', 'size_L']
    
    # Assert the shape of the DataFrame
    assert encoded_df.shape == (3, 6)
    
    # Assert the presence of the expected columns
    assert all(col in encoded_df.columns for col in expected_columns)
    
    # Assert that the original columns are dropped
    assert not any(col in encoded_df.columns for col in ['color', 'size'])

def test_one_hot_encode_empty_dataframe():
    # Create an empty DataFrame
    df = pd.DataFrame()
    
    # Initialize the encoder and perform one-hot encoding
    encoder = CategoricalDataEncoder(df)
    encoded_df = encoder.one_hot_encode(['color'])
    
    # Assert that the output is None if no columns are provided
    assert encoded_df is None

def test_one_hot_encode_nonexistent_columns():
    # Create a sample DataFrame with categorical columns
    data = {
        'color': ['red', 'blue', 'green'],
        'size': ['S', 'M', 'L']
    }
    df = pd.DataFrame(data)
    
    # Initialize the encoder and attempt to encode non-existent columns
    encoder = CategoricalDataEncoder(df)
    encoded_df = encoder.one_hot_encode(['color', 'non_existent'])
    
    # Assert that no new columns are added for non-existent columns
    assert all(col in df.columns for col in ['color', 'size'])

# Add more tests as needed to cover additional edge cases and error paths