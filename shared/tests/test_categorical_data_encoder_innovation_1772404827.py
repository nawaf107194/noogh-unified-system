import pytest
import pandas as pd
from shared.categorical_data_encoder import CategoricalDataEncoder

@pytest.fixture
def sample_df():
    data = {
        'A': ['a', 'b', 'c'],
        'B': [1, 2, 3],
        'C': ['x', 'y']
    }
    return pd.DataFrame(data)

def test_happy_path(sample_df):
    encoder = CategoricalDataEncoder(sample_df)
    result = encoder.one_hot_encode(columns=['A', 'C'])
    expected_columns = ['B', 'A_a', 'A_b', 'A_c', 'C_x', 'C_y']
    assert result.columns.tolist() == expected_columns
    assert (result['A_a'] == [1, 0, 0]).all()
    assert (result['A_b'] == [0, 1, 0]).all()
    assert (result['A_c'] == [0, 0, 1]).all()
    assert (result['C_x'] == [1, 0]).all()
    assert (result['C_y'] == [0, 1]).all()

def test_no_columns_to_encode(sample_df):
    encoder = CategoricalDataEncoder(sample_df)
    result = encoder.one_hot_encode(columns=[])
    expected_columns = ['A', 'B', 'C']
    assert result.columns.tolist() == expected_columns
    assert (result['A'] == sample_df['A']).all()
    assert (result['B'] == sample_df['B']).all()
    assert (result['C'] == sample_df['C']).all()

def test_default_encode_all_categorical(sample_df):
    encoder = CategoricalDataEncoder(sample_df)
    result = encoder.one_hot_encode()
    expected_columns = ['A', 'B', 'C_a', 'C_y']
    assert result.columns.tolist() == expected_columns
    assert (result['C_a'] == [1, 0]).all()
    assert (result['C_y'] == [0, 1]).all()

def test_empty_dataframe():
    df = pd.DataFrame()
    encoder = CategoricalDataEncoder(df)
    result = encoder.one_hot_encode()
    assert result is None

def test_none_columns():
    df = pd.DataFrame({'A': ['a', 'b', 'c'], 'B': [1, 2, 3]})
    encoder = CategoricalDataEncoder(df)
    result = encoder.one_hot_encode(columns=None)
    expected_columns = ['A_a', 'A_b', 'A_c']
    assert result.columns.tolist() == expected_columns
    assert (result['A_a'] == [1, 0, 0]).all()
    assert (result['A_b'] == [0, 1, 0]).all()
    assert (result['A_c'] == [0, 0, 1]).all()

def test_invalid_column_name():
    encoder = CategoricalDataEncoder(sample_df)
    result = encoder.one_hot_encode(columns=['D'])
    expected_columns = ['A', 'B', 'C']
    assert result.columns.tolist() == expected_columns
    assert (result['A'] == sample_df['A']).all()
    assert (result['B'] == sample_df['B']).all()
    assert (result['C'] == sample_df['C']).all()

def test_non_categorical_column():
    df = pd.DataFrame({'A': ['a', 'b', 'c'], 'B': [1, 2, 3], 'D': [4.0, 5.0, 6.0]})
    encoder = CategoricalDataEncoder(df)
    result = encoder.one_hot_encode(columns=['A', 'D'])
    expected_columns = ['B', 'A_a', 'A_b', 'A_c']
    assert result.columns.tolist() == expected_columns
    assert (result['A_a'] == [1, 0, 0]).all()
    assert (result['A_b'] == [0, 1, 0]).all()
    assert (result['A_c'] == [0, 0, 1]).all()