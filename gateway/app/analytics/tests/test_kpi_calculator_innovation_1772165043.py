from typing import List, Dict, Optional
import statistics
import math

def _calc_avg_confidence(events: List[Dict]) -> Optional[float]:
    """Average decision confidence."""
    decisions = [e for e in events if e.get('type') == 'decision']
    confidences = [d.get('payload', {}).get('confidence', 0) for d in decisions]
    confidences = [c for c in confidences if c > 0]  # Filter zeros
    
    if not confidences:
        return None
    
    return round(statistics.mean(confidences), 3)

# Test cases
def test_calc_avg_confidence_happy_path():
    events = [
        {'type': 'decision', 'payload': {'confidence': 0.8}},
        {'type': 'decision', 'payload': {'confidence': 0.7}},
        {'type': 'other', 'payload': {}}
    ]
    assert _calc_avg_confidence(events) == 0.75

def test_calc_avg_confidence_empty():
    events = []
    assert _calc_avg_confidence(events) is None

def test_calc_avg_confidence_none_input():
    assert _calc_avg_confidence(None) is None

def test_calc_avg_confidence_only_zeros():
    events = [
        {'type': 'decision', 'payload': {'confidence': 0}},
        {'type': 'decision', 'payload': {'confidence': 0}}
    ]
    assert _calc_avg_confidence(events) is None

def test_calc_avg_confidence_boundary_values():
    events = [
        {'type': 'decision', 'payload': {'confidence': 1.0}},
        {'type': 'decision', 'payload': {'confidence': 0.999}}
    ]
    assert _calc_avg_confidence(events) == round((1.0 + 0.999) / 2, 3)

def test_calc_avg_confidence_negative_values():
    events = [
        {'type': 'decision', 'payload': {'confidence': -0.5}},
        {'type': 'decision', 'payload': {'confidence': -1.0}}
    ]
    assert _calc_avg_confidence(events) is None