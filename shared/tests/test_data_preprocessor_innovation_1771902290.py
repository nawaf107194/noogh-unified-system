import pytest
import pandas as pd
import numpy as np

from shared.data_preprocessor import sqrt_transform

def test_sqrt_transform_happy_path():
    data = pd.DataFrame({
        'A': [1, 4, 9],
        'B': [16, 25, 36]
    })
    expected = pd.DataFrame({
        'A': [1.0, 2.0, 3.0],
        'B': [4.0, 5.0, 6.0]
    })
    result = sqrt_transform(data)
    assert result.equals(expected)

def test_sqrt_transform_empty_data():
    data = pd.DataFrame()
    expected = pd.DataFrame()
    result = sqrt_transform(data)
    assert result.equals(expected)

def test_sqrt_transform_none_input():
    data = None
    result = sqrt_transform(data)
    assert result is None

def test_sqrt_transform_single_value_array():
    data = np.array([1, 4, 9])
    expected = np.array([1.0, 2.0, 3.0])
    result = sqrt_transform(data)
    assert np.allclose(result, expected)

def test_sqrt_transform_single_value_dataframe():
    data = pd.DataFrame({'A': [1]})
    expected = pd.DataFrame({'A': [1.0]})
    result = sqrt_transform(data)
    assert result.equals(expected)

def test_sqrt_transform_non_numeric_data():
    data = pd.DataFrame({
        'A': ['a', 'b', 'c'],
        'B': [1, 2, 3]
    })
    expected = pd.DataFrame({
        'A': [np.nan, np.nan, np.nan],
        'B': [1.0, 2.0, 3.0]
    })
    result = sqrt_transform(data)
    assert result.equals(expected)

def test_sqrt_transform_negative_values():
    data = pd.DataFrame({'A': [-1, -4, -9]})
    result = sqrt_transform(data)
    expected = pd.DataFrame({'A': [np.nan, np.nan, np.nan]})
    assert result.equals(expected)