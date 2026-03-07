import pytest
import numpy as np
import pandas as pd

def log_transform(data):
    """
    Apply logarithmic transformation to the data.

    :param data: DataFrame or array-like input data.
    :return: Transformed data.
    """
    if isinstance(data, pd.DataFrame):
        return data.apply(lambda x: np.log(x + 1))
    else:
        return np.log(data + 1)

@pytest.mark.parametrize("data, expected", [
    (pd.Series([1, 2, 3]), pd.Series([0., 0.693147, 1.098612])),
    (pd.DataFrame({'A': [1, 2], 'B': [3, 4]}), pd.DataFrame({'A': [0., 0.693147], 'B': [1.098612, 1.386294]})),
    (np.array([1, 2, 3]), np.array([0., 0.693147, 1.098612])),
    ([1, 2, 3], [0., 0.693147, 1.098612]),
])
def test_log_transform_happy_path(data, expected):
    result = log_transform(data)
    pd.testing.assert_series_equal(result, expected, rtol=1e-5) if isinstance(result, pd.Series) else np.testing.assert_array_almost_equal(result, expected, decimal=5)

@pytest.mark.parametrize("data", [
    pd.Series([]),
    pd.DataFrame({'A': []}),
    [],
    (),
    None,
])
def test_log_transform_edge_cases(data):
    result = log_transform(data)
    assert result is None

@pytest.mark.parametrize("data, error_type", [
    (pd.Series([-1, 2, 3]), TypeError),
    ([0], ValueError),
    ("abc", TypeError),
    ({}, TypeError),
])
def test_log_transform_error_cases(data, error_type):
    with pytest.raises(error_type):
        log_transform(data)