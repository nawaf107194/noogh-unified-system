import pytest

def long_filter(s):
    atr = s.get('atr', 0)
    tbr = s.get('taker_buy_ratio', 0)
    if atr < 5 or tbr < 0.5:
        return False, 0.0, 'ATR too low or TBR below threshold'
    return True, min(1.0, atr / 100), 'Long conditions met'

def test_long_filter_happy_path():
    input_data = {'atr': 6, 'taker_buy_ratio': 0.6}
    expected_result = (True, 0.06, 'Long conditions met')
    assert long_filter(input_data) == expected_result

def test_long_filter_edge_cases_empty_input():
    input_data = {}
    expected_result = (False, 0.0, 'ATR too low or TBR below threshold')
    assert long_filter(input_data) == expected_result

def test_long_filter_edge_cases_none_input():
    with pytest.raises(TypeError):
        long_filter(None)

def test_long_filter_edge_cases_boundary_atr_min():
    input_data = {'atr': 5, 'taker_buy_ratio': 0.6}
    expected_result = (False, 0.0, 'ATR too low or TBR below threshold')
    assert long_filter(input_data) == expected_result

def test_long_filter_edge_cases_boundary_tbr_min():
    input_data = {'atr': 6, 'taker_buy_ratio': 0.5}
    expected_result = (False, 0.0, 'ATR too low or TBR below threshold')
    assert long_filter(input_data) == expected_result

def test_long_filter_error_cases_invalid_input_type():
    with pytest.raises(TypeError):
        long_filter('not a dictionary')

def test_long_filter_error_cases_missing_key_atr():
    input_data = {'taker_buy_ratio': 0.6}
    expected_result = (False, 0.0, 'ATR too low or TBR below threshold')
    assert long_filter(input_data) == expected_result

def test_long_filter_error_cases_missing_key_tbr():
    input_data = {'atr': 6}
    expected_result = (True, 0.06, 'Long conditions met')
    assert long_filter(input_data) == expected_result