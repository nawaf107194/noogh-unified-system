import pytest

def long_filter(s):
    atr = s.get('avg_atr', 0)
    vol_regime = s.get('volatility_regime', 'MEDIUM')
    if vol_regime == 'LOW' and atr < 0.006: return False, 0.0, 'Low ATR in Low Volatility'
    if vol_regime != 'LOW': return False, 0.0, 'Not Low Volatility'
    return True, min(1.0, atr / 0.06), 'ATR within range'

# Tests

def test_long_filter_happy_path():
    input_data = {
        'avg_atr': 0.007,
        'volatility_regime': 'LOW'
    }
    expected_output = (True, min(1.0, 0.007 / 0.06), 'ATR within range')
    assert long_filter(input_data) == expected_output

def test_long_filter_low_volatility_low_atr():
    input_data = {
        'avg_atr': 0.005,
        'volatility_regime': 'LOW'
    }
    expected_output = (False, 0.0, 'Low ATR in Low Volatility')
    assert long_filter(input_data) == expected_output

def test_long_filter_not_low_volatility():
    input_data = {
        'avg_atr': 0.010,
        'volatility_regime': 'HIGH'
    }
    expected_output = (False, 0.0, 'Not Low Volatility')
    assert long_filter(input_data) == expected_output

def test_long_filter_empty_input():
    input_data = {}
    expected_output = (False, 0.0, 'Not Low Volatility')
    assert long_filter(input_data) == expected_output

def test_long_filter_none_input():
    input_data = None
    expected_output = (False, 0.0, 'Not Low Volatility')
    assert long_filter(input_data) == expected_output

def test_long_filter_boundary_atr():
    input_data = {
        'avg_atr': 0.06,
        'volatility_regime': 'LOW'
    }
    expected_output = (True, min(1.0, 0.06 / 0.06), 'ATR within range')
    assert long_filter(input_data) == expected_output