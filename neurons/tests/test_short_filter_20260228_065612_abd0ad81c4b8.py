import pytest

def short_filter(s):
    vol = s.get('avg_vol', 0)
    side = s.get('dominant_side', 'NEUTRAL')
    if side == 'NEUTRAL' and vol < 12000: return False, 0.0, 'Neutral Side with Low Volume'
    if side != 'NEUTRAL': return False, 0.0, 'Not Neutral Side'
    return True, min(1.0, vol / 120000), 'Volume within range'

def test_short_filter_happy_path():
    assert short_filter({'avg_vol': 15000, 'dominant_side': 'RIGHT'}) == (True, 0.125, 'Volume within range')
    assert short_filter({'avg_vol': 8000, 'dominant_side': 'LEFT'}) == (False, 0.0, 'Not Neutral Side')

def test_short_filter_edge_cases():
    assert short_filter({'avg_vol': 12000, 'dominant_side': 'NEUTRAL'}) == (True, 0.1, 'Volume within range')
    assert short_filter({'avg_vol': 12000, 'dominant_side': 'RIGHT'}) == (True, 0.1, 'Volume within range')
    assert short_filter({'avg_vol': 12000, 'dominant_side': 'LEFT'}) == (True, 0.1, 'Volume within range')

def test_short_filter_error_cases():
    assert short_filter(None) == (False, 0.0, 'Not Neutral Side')
    assert short_filter({}) == (False, 0.0, 'Not Neutral Side')
    assert short_filter({'avg_vol': None, 'dominant_side': 'RIGHT'}) == (False, 0.0, 'Not Neutral Side')
    assert short_filter({'avg_vol': 15000, 'dominant_side': None}) == (False, 0.0, 'Not Neutral Side')

def test_short_filter_boundary_cases():
    assert short_filter({'avg_vol': 12000, 'dominant_side': 'NEUTRAL'}) == (True, 0.1, 'Volume within range')
    assert short_filter({'avg_vol': 0, 'dominant_side': 'LEFT'}) == (False, 0.0, 'Not Neutral Side')