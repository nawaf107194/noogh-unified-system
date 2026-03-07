import pytest
import numpy as np
import pandas as pd

from shared.data_preprocessor import log_transform

def test_log_transform_happy_path():
    data = pd.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6]
    })
    transformed_data = log_transform(data)
    assert isinstance(transformed_data, pd.DataFrame)
    np.testing.assert_array_almost_equal(
        transformed_data.values,
        np.log(data.values + 1),
        decimal=5
    )

def test_log_transform_empty_dataframe():
    data = pd.DataFrame()
    transformed_data = log_transform(data)
    assert transformed_data.empty

def test_log_transform_none_input():
    transformed_data = log_transform(None)
    assert transformed_data is None

def test_log_transform_array_like_input():
    data = [1, 2, 3]
    transformed_data = log_transform(data)
    np.testing.assert_array_almost_equal(
        transformed_data,
        np.log(np.array(data) + 1),
        decimal=5
    )

def test_log_transform_boundary_values():
    data = pd.DataFrame({
        'A': [0.0001, 1, 100]
    })
    transformed_data = log_transform(data)
    assert isinstance(transformed_data, pd.DataFrame)
    np.testing.assert_array_almost_equal(
        transformed_data.values,
        np.log(data.values + 1),
        decimal=5
    )

# Error cases are not applicable as the function does not explicitly raise exceptions for invalid inputs.