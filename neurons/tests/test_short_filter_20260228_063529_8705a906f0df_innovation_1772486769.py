import pytest

def short_filter(s):
    vol = s.get('avg_vol', 0)
    side = s.get('dominant_side', 'NEUTRAL')
    if side == 'NEUTRAL' and vol < 10000: return False, 0.0, 'Neutral Side with Low Volume'
    if side != 'NEUTRAL': return False, 0.0, 'Not Neutral Side'
    return True, min(1.0, vol / 100000), 'Volume within range'

def test_short_filter_happy_path():
    input_data = {'avg_vol': 5000, 'dominant_side': 'LEFT'}
    expected_output = (True, 0.05, 'Volume within range')
    assert short_filter(input_data) == expected_output

def test_short_filter_neutral_low_volume():
    input_data = {'avg_vol': 9000, 'dominant_side': 'NEUTRAL'}
    expected_output = (False, 0.0, 'Neutral Side with Low Volume')
    assert short_filter(input_data) == expected_output

def test_short_filter_non_neutral():
    input_data = {'avg_vol': 15000, 'dominant_side': 'RIGHT'}
    expected_output = (False, 0.0, 'Not Neutral Side')
    assert short_filter(input_data) == expected_output

def test_short_filter_empty_input():
    input_data = {}
    expected_output = (True, 0.0, 'Volume within range')
    assert short_filter(input_data) == expected_output

def test_short_filter_none_input():
    input_data = None
    expected_output = (True, 0.0, 'Volume within range')
    assert short_filter(input_data) == expected_output

def test_short_filter_boundary_high_volume():
    input_data = {'avg_vol': 100000, 'dominant_side': 'LEFT'}
    expected_output = (True, 1.0, 'Volume within range')
    assert short_filter(input_data) == expected_output