import pytest
import pandas as pd

from shared.data_preprocessor import DataPreprocessor

def test_encode_happy_path():
    dp = DataPreprocessor({'onehot': OneHotEncoder()})
    data = pd.DataFrame({'A': ['a', 'b', 'c']})
    encoded_data = dp.encode(data)
    expected_columns = ['A_a', 'A_b', 'A_c']
    assert isinstance(encoded_data, pd.DataFrame)
    assert list(encoded_data.columns) == expected_columns
    assert (encoded_data.sum(axis=1) == 1).all()

def test_encode_empty_data():
    dp = DataPreprocessor({'onehot': OneHotEncoder()})
    data = pd.DataFrame()
    encoded_data = dp.encode(data)
    assert isinstance(encoded_data, pd.DataFrame)
    assert encoded_data.empty

def test_encode_none_input():
    dp = DataPreprocessor({'onehot': OneHotEncoder()})
    encoded_data = dp.encode(None)
    assert encoded_data is None

def test_encode_invalid_method():
    dp = DataPreprocessor({})
    data = pd.DataFrame({'A': ['a', 'b', 'c']})
    with pytest.raises(KeyError):
        dp.encode(data, method='invalid')

def test_encode_single_value():
    dp = DataPreprocessor({'onehot': OneHotEncoder()})
    data = pd.Series(['a'], name='A')
    encoded_data = dp.encode(data)
    assert isinstance(encoded_data, np.ndarray)
    assert encoded_data.shape == (1, 1)

def test_encode_with_missing_values():
    dp = DataPreprocessor({'onehot': OneHotEncoder(sparse=False)})
    data = pd.DataFrame({'A': ['a', None, 'c']})
    encoded_data = dp.encode(data)
    assert isinstance(encoded_data, np.ndarray)
    assert (encoded_data[:, 1] == 0).all()  # Missing value should be encoded as 0