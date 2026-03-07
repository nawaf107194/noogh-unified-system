import pytest
import pandas as pd

from trading.regimes import _rsi, _ema

def test_rsi_happy_path():
    close_prices = pd.Series([100, 102, 105, 104, 103, 107, 110, 108, 112, 115])
    expected_output = pd.Series([nan, nan, nan, nan, nan, nan, nan, 69.117647, 74.927451, 31.882353], dtype='float64')
    result = _rsi(close_prices)
    pd.testing.assert_series_equal(result, expected_output)

def test_rsi_empty_input():
    close_prices = pd.Series([])
    expected_output = pd.Series([], dtype='float64')
    result = _rsi(close_prices)
    pd.testing.assert_series_equal(result, expected_output)

def test_rsi_none_input():
    close_prices = None
    with pytest.raises(TypeError):
        _rsi(close_prices)

def test_rsi_boundary_period_1():
    close_prices = pd.Series([100])
    expected_output = pd.Series([nan], dtype='float64')
    result = _rsi(close_prices, period=1)
    pd.testing.assert_series_equal(result, expected_output)

def test_rsi_boundary_period_large():
    close_prices = pd.Series([100] * 20)
    expected_output = pd.Series([nan] * 20, dtype='float64')
    result = _rsi(close_prices, period=20)
    pd.testing.assert_series_equal(result, expected_output)

def test_rsi_negative_period():
    close_prices = pd.Series([100])
    with pytest.raises(ValueError):
        _rsi(close_prices, period=-1)

def test_rsi_non_numeric_input():
    close_prices = pd.Series(['a', 'b', 'c'])
    with pytest.raises(TypeError):
        _rsi(close_prices)