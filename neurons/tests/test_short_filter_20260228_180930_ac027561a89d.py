import pytest

from neurons.short_filter_20260228_180930_ac027561a89d import short_filter

def test_short_filter_happy_path():
    s = {'vol_z': 2, 'atr_1h_pct': 0.01}
    result = short_filter(s)
    assert result == (True, 0.02, 'Good Volume and ATR')

def test_short_filter_low_volume():
    s = {'vol_z': 0.5, 'atr_1h_pct': 0.01}
    result = short_filter(s)
    assert result == (False, 0.0, 'Low Volume or ATR')

def test_short_filter_low_atr():
    s = {'vol_z': 2, 'atr_1h_pct': 0.004}
    result = short_filter(s)
    assert result == (False, 0.0, 'Low Volume or ATR')

def test_short_filter_zero_volume_and_atr():
    s = {'vol_z': 0, 'atr_1h_pct': 0}
    result = short_filter(s)
    assert result == (False, 0.0, 'Low Volume or ATR')

def test_short_filter_none_input():
    result = short_filter(None)
    assert result == (False, 0.0, 'Low Volume or ATR')

def test_short_filter_empty_dict():
    result = short_filter({})
    assert result == (False, 0.0, 'Low Volume or ATR')

def test_short_filter_negative_volume():
    s = {'vol_z': -1, 'atr_1h_pct': 0.01}
    result = short_filter(s)
    assert result == (False, 0.0, 'Low Volume or ATR')

def test_short_filter_negative_atr():
    s = {'vol_z': 2, 'atr_1h_pct': -0.01}
    result = short_filter(s)
    assert result == (False, 0.0, 'Low Volume or ATR')

def test_short_filter_small_volume_large_atr():
    s = {'vol_z': 0.5, 'atr_1h_pct': 2.0}
    result = short_filter(s)
    assert result == (True, 1.0, 'Good Volume and ATR')