import pytest

def long_filter(s):
    atr = s.get('avg_atr', 0)
    vol_regime = s.get('volatility_regime', 'MEDIUM')
    if vol_regime == 'LOW' and atr < 0.006: return False, 0.0, 'Low ATR in Low Volatility'
    if vol_regime != 'LOW': return False, 0.0, 'Not Low Volatility'
    return True, min(1.0, atr / 0.06), 'ATR within range'

def test_long_filter_happy_path():
    input_data = {
        'avg_atr': 0.005,
        'volatility_regime': 'LOW'
    }
    expected_output = (False, 0.0, 'Low ATR in Low Volatility')
    assert long_filter(input_data) == expected_output

def test_long_filter_edge_case_low_volatility():
    input_data = {
        'avg_atr': 0.007,
        'volatility_regime': 'LOW'
    }
    expected_output = (False, 0.0, 'Not Low Volatility')
    assert long_filter(input_data) == expected_output

def test_long_filter_edge_case_not_low_volatility():
    input_data = {
        'avg_atr': 0.005,
        'volatility_regime': 'MEDIUM'
    }
    expected_output = (True, min(1.0, 0.005 / 0.06), 'ATR within range')
    assert long_filter(input_data) == expected_output

def test_long_filter_edge_case_empty_input():
    input_data = {}
    expected_output = (False, 0.0, 'Not Low Volatility')
    assert long_filter(input_data) == expected_output

def test_long_filter_edge_case_none_input():
    input_data = None
    with pytest.raises(TypeError):
        long_filter(input_data)

def test_long_filter_edge_case_boundary_atr_lowest():
    input_data = {
        'avg_atr': 0.006,
        'volatility_regime': 'LOW'
    }
    expected_output = (False, 0.0, 'Low ATR in Low Volatility')
    assert long_filter(input_data) == expected_output

def test_long_filter_edge_case_boundary_atr_highest():
    input_data = {
        'avg_atr': 0.12,
        'volatility_regime': 'LOW'
    }
    expected_output = (True, 2.0, 'ATR within range')
    assert long_filter(input_data) == expected_output