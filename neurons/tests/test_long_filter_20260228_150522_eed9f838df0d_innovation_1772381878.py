import pytest

from neurons.long_filter_20260228_150522_eed9f838df0d import long_filter

def test_long_filter_happy_path():
    # Normal inputs within range
    result = long_filter({'atr': 7, 'rsi': 65})
    assert result == (True, 0.07, 'ATR and RSI within range')

def test_long_filter_edge_case_atr_too_low():
    # ATR below threshold
    result = long_filter({'atr': 5, 'rsi': 65})
    assert result == (False, 0.0, 'ATR too low or RSI too high')

def test_long_filter_edge_case_rsi_too_high():
    # RSI above threshold
    result = long_filter({'atr': 7, 'rsi': 69})
    assert result == (False, 0.0, 'ATR too low or RSI too high')

def test_long_filter_edge_case_empty_input():
    # Empty dictionary
    result = long_filter({})
    assert result == (False, 0.0, 'ATR too low or RSI too high')

def test_long_filter_edge_case_none_input():
    # None input
    with pytest.raises(TypeError):
        result = long_filter(None)

def test_long_filter_edge_case_boundary_atr():
    # ATR at boundary
    result = long_filter({'atr': 6, 'rsi': 65})
    assert result == (True, 0.06, 'ATR and RSI within range')

def test_long_filter_edge_case_boundary_rsi():
    # RSI at boundary
    result = long_filter({'atr': 7, 'rsi': 68})
    assert result == (False, 0.0, 'ATR too low or RSI too high')