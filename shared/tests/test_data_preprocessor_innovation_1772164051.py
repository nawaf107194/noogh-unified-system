import numpy as np
import pandas as pd
import pytest

def sqrt_transform(data):
    """
    Apply square root transformation to the data.

    :param data: DataFrame or array-like input data.
    :return: Transformed data.
    """
    if isinstance(data, pd.DataFrame):
        return data.apply(lambda x: np.sqrt(x))
    else:
        return np.sqrt(data)

def test_sqrt_transform_happy_path():
    # Test with a pandas DataFrame
    df = pd.DataFrame({'A': [1, 4, 9], 'B': [16, 25, 36]})
    result = sqrt_transform(df)
    expected = pd.DataFrame({'A': [1.0, 2.0, 3.0], 'B': [4.0, 5.0, 6.0]})
    assert result.equals(expected)

    # Test with a numpy array
    arr = np.array([1, 4, 9])
    result = sqrt_transform(arr)
    expected = np.array([1.0, 2.0, 3.0])
    assert np.allclose(result, expected)

def test_sqrt_transform_edge_cases():
    # Test with an empty DataFrame
    df_empty = pd.DataFrame()
    result = sqrt_transform(df_empty)
    assert result.empty

    # Test with None input
    result_none = sqrt_transform(None)
    assert result_none is None

def test_sqrt_transform_error_cases():
    # Test with a non-numeric pandas DataFrame
    df_non_numeric = pd.DataFrame({'A': ['a', 'b', 'c'], 'B': [1, 2, 3]})
    result = sqrt_transform(df_non_numeric)
    expected = pd.DataFrame({'A': np.nan, 'B': [np.sqrt(1), np.sqrt(2), np.sqrt(3)]})
    assert result.equals(expected)

    # Test with a non-numeric numpy array
    arr_non_numeric = np.array(['a', 'b', 'c'])
    result = sqrt_transform(arr_non_numeric)
    expected = np.nan
    assert np.isnan(result)