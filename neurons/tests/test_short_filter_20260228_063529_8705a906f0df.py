import pytest

from neurons.short_filter_20260228_063529_8705a906f0df import short_filter

def test_happy_path():
    s = {'avg_vol': 15000, 'dominant_side': 'RIGHT'}
    result = short_filter(s)
    assert result == (True, 0.15, 'Volume within range')

def test_edge_cases_empty_input():
    s = {}
    result = short_filter(s)
    assert result == (False, 0.0, 'Neutral Side with Low Volume')

def test_edge_cases_none_input():
    s = None
    result = short_filter(s)
    assert result is None

def test_edge_cases_boundary_volume_low():
    s = {'avg_vol': 5000, 'dominant_side': 'LEFT'}
    result = short_filter(s)
    assert result == (False, 0.0, 'Neutral Side with Low Volume')

def test_edge_cases_boundary_volume_high():
    s = {'avg_vol': 100000, 'dominant_side': 'NEUTRAL'}
    result = short_filter(s)
    assert result == (True, 1.0, 'Volume within range')

def test_error_case_invalid_input_type():
    s = 'not a dictionary'
    result = short_filter(s)
    assert result is None