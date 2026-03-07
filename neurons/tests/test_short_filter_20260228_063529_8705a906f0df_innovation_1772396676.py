import pytest

from neurons.short_filter_20260228_063529_8705a906f0df import short_filter

def test_short_filter_happy_path():
    sample_input = {'avg_vol': 15000, 'dominant_side': 'LEFT'}
    result = short_filter(sample_input)
    assert result == (True, 0.15, 'Volume within range')

def test_short_filter_neutral_side_low_volume():
    sample_input = {'avg_vol': 8000, 'dominant_side': 'NEUTRAL'}
    result = short_filter(sample_input)
    assert result == (False, 0.0, 'Neutral Side with Low Volume')

def test_short_filter_non_neutral_side():
    sample_input = {'avg_vol': 15000, 'dominant_side': 'RIGHT'}
    result = short_filter(sample_input)
    assert result == (False, 0.0, 'Not Neutral Side')

def test_short_filter_empty_input():
    result = short_filter({})
    assert result == (True, 0.0, 'Volume within range')  # Assuming avg_vol defaults to 0

def test_short_filter_none_input():
    result = short_filter(None)
    assert result == (True, 0.0, 'Volume within range')  # Assuming avg_vol defaults to 0

def test_short_filter_boundary_volume():
    sample_input = {'avg_vol': 10000, 'dominant_side': 'NEUTRAL'}
    result = short_filter(sample_input)
    assert result == (True, 0.1, 'Volume within range')

def test_short_filter_non_numerical_avg_vol():
    # Assuming the function handles non-numerical values gracefully
    sample_input = {'avg_vol': 'abc', 'dominant_side': 'LEFT'}
    result = short_filter(sample_input)
    assert result == (True, 0.0, 'Volume within range')  # Assuming avg_vol defaults to 0

def test_short_filter_non_string_dominant_side():
    sample_input = {'avg_vol': 15000, 'dominant_side': 123}
    result = short_filter(sample_input)
    assert result == (True, 0.0, 'Volume within range')  # Assuming dominant_side defaults to 'NEUTRAL'

def test_short_filter_missing_keys():
    sample_input = {'avg_vol': 15000}
    result = short_filter(sample_input)
    assert result == (True, 0.0, 'Volume within range')  # Assuming missing keys are handled gracefully