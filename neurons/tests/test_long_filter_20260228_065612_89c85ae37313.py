import pytest

def long_filter(s):
    atr = s.get('avg_atr', 0)
    vol_regime = s.get('volatility_regime', 'MEDIUM')
    if vol_regime == 'LOW' and atr < 0.006: return False, 0.0, 'Low ATR in Low Volatility'
    if vol_regime != 'LOW': return False, 0.0, 'Not Low Volatility'
    return True, min(1.0, atr / 0.06), 'ATR within range'

def test_long_filter_happy_path():
    input_data = {
        'avg_atr': 0.05,
        'volatility_regime': 'LOW'
    }
    expected_output = (True, 0.8333333333333334, 'ATR within range')
    assert long_filter(input_data) == expected_output

def test_long_filter_edge_case_low_atr():
    input_data = {
        'avg_atr': 0.005,
        'volatility_regime': 'LOW'
    }
    expected_output = (False, 0.0, 'Low ATR in Low Volatility')
    assert long_filter(input_data) == expected_output

def test_long_filter_edge_case_not_low_volatility():
    input_data = {
        'avg_atr': 0.05,
        'volatility_regime': 'HIGH'
    }
    expected_output = (False, 0.0, 'Not Low Volatility')
    assert long_filter(input_data) == expected_output

def test_long_filter_edge_case_empty_input():
    input_data = {}
    expected_output = (False, 0.0, 'Not Low Volatility')
    assert long_filter(input_data) == expected_output

def test_long_filter_async_behavior_not_applicable():
    # Since the function is synchronous and does not involve any async behavior,
    # there's no need for a separate test case for async behavior.
    pass