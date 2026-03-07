import pytest

from neurons.short_filter_20260228_150522_c1d9d6329fc8 import short_filter

def test_happy_path():
    data = {'volume': 2500000, 'taker_buy_ratio': 0.4}
    result = short_filter(data)
    assert result == (True, 0.5, 'Volume and TBR within range')

def test_volume_too_low():
    data = {'volume': 2000000, 'taker_buy_ratio': 0.4}
    result = short_filter(data)
    assert result == (False, 0.0, 'Volume too low or TBR too high')

def test_tbr_too_high():
    data = {'volume': 3000000, 'taker_buy_ratio': 0.5}
    result = short_filter(data)
    assert result == (False, 0.0, 'Volume too low or TBR too high')

def test_empty_dict():
    data = {}
    result = short_filter(data)
    assert result == (False, 0.0, 'Volume too low or TBR too high')

def test_none_input():
    result = short_filter(None)
    assert result == (False, 0.0, 'Volume too low or TBR too high')

def test_boundary_volume():
    data = {'volume': 2250000, 'taker_buy_ratio': 0.475}
    result = short_filter(data)
    assert result == (True, 0.45, 'Volume and TBR within range')

def test_boundary_tbr():
    data = {'volume': 3000000, 'taker_buy_ratio': 0.475}
    result = short_filter(data)
    assert result == (False, 0.0, 'Volume too low or TBR too high')