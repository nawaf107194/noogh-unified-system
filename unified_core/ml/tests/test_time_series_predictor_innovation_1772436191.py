import pytest
import numpy as np

from unified_core.ml.time_series_predictor import TimeSeriesPredictor

@pytest.fixture
def predictor():
    return TimeSeriesPredictor(scaler_mean=0.5, scaler_std=1.0)

def test_denormalize_happy_path(predictor):
    data = np.array([0.0, 1.0, 2.0])
    denormalized_data = predictor._denormalize(data)
    expected_output = np.array([-0.5, 1.5, 2.5])
    assert np.allclose(denormalized_data, expected_output)

def test_denormalize_empty_input(predictor):
    data = np.array([])
    result = predictor._denormalize(data)
    assert np.array_equal(result, data)

def test_denormalize_none_input(predictor):
    data = None
    result = predictor._denormalize(data)
    assert result is None

def test_denormalize_boundary_values(predictor):
    data = np.array([-1.0, 0.0, 1.0])
    denormalized_data = predictor._denormalize(data)
    expected_output = np.array([-2.5, -0.5, 2.5])
    assert np.allclose(denormalized_data, expected_output)

def test_denormalize_no_scaler(predictor):
    predictor.scaler_mean = None
    predictor.scaler_std = None
    data = np.array([0.0, 1.0, 2.0])
    result = predictor._denormalize(data)
    assert np.array_equal(result, data)