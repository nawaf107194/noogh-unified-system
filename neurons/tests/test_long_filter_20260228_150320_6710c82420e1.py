import pytest

def long_filter(s):
    atr = s.get('atr', 0)
    rsi = s.get('rsi', 50)
    if atr < 5 or rsi > 70: return False, 0.0, 'ATR too low or RSI too high'
    return True, min(1.0, atr / 100), 'ATR and RSI within range'

def test_long_filter_happy_path():
    test_data = {'atr': 6, 'rsi': 65}
    expected_result = (True, 0.06, 'ATR and RSI within range')
    assert long_filter(test_data) == expected_result

def test_long_filter_edge_case_empty_input():
    test_data = {}
    expected_result = (False, 0.0, 'ATR too low or RSI too high')
    assert long_filter(test_data) == expected_result

def test_long_filter_edge_case_none_input():
    test_data = None
    result = long_filter(test_data)
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert all(isinstance(x, (bool, float)) for x in result[0:2])
    assert isinstance(result[2], str)

def test_long_filter_edge_case_boundary_atr_low():
    test_data = {'atr': 4.9, 'rsi': 65}
    expected_result = (False, 0.0, 'ATR too low or RSI too high')
    assert long_filter(test_data) == expected_result

def test_long_filter_edge_case_boundary_atr_high():
    test_data = {'atr': 100, 'rsi': 65}
    expected_result = (True, 1.0, 'ATR and RSI within range')
    assert long_filter(test_data) == expected_result

def test_long_filter_edge_case_boundary_rsi_low():
    test_data = {'atr': 7, 'rsi': 49}
    expected_result = (False, 0.0, 'ATR too low or RSI too high')
    assert long_filter(test_data) == expected_result

def test_long_filter_edge_case_boundary_rsi_high():
    test_data = {'atr': 7, 'rsi': 71}
    expected_result = (False, 0.0, 'ATR too low or RSI too high')
    assert long_filter(test_data) == expected_result