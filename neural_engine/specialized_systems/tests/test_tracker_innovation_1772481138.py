import pytest

from neural_engine.specialized_systems.tracker import Tracker

def test_get_low_hours_happy_path():
    tracker = Tracker()
    tracker.daily_patterns = {
        0: [1.5, 2.0, 3.0],
        1: [4.0, 5.0, 6.0],
        2: [7.0, 8.0, 9.0]
    }
    result = tracker.get_low_hours(bottom_n=2)
    assert result == [(0, 2.0), (1, 5.0)]

def test_get_low_hours_empty_input():
    tracker = Tracker()
    tracker.daily_patterns = {}
    result = tracker.get_low_hours(bottom_n=2)
    assert result == []

def test_get_low_hours_bottom_n_zero():
    tracker = Tracker()
    tracker.daily_patterns = {
        0: [1.5, 2.0, 3.0],
        1: [4.0, 5.0, 6.0]
    }
    result = tracker.get_low_hours(bottom_n=0)
    assert result == []

def test_get_low_hours_boundary_bottom_n():
    tracker = Tracker()
    tracker.daily_patterns = {
        0: [1.5, 2.0, 3.0],
        1: [4.0, 5.0, 6.0]
    }
    result = tracker.get_low_hours(bottom_n=1)
    assert result == [(0, 2.0)]

def test_get_low_hours_invalid_bottom_n():
    tracker = Tracker()
    tracker.daily_patterns = {
        0: [1.5, 2.0, 3.0],
        1: [4.0, 5.0, 6.0]
    }
    result = tracker.get_low_hours(bottom_n=-1)
    assert result == []

def test_get_low_hours_no_daily_patterns():
    tracker = Tracker()
    result = tracker.get_low_hours(bottom_n=2)
    assert result == []

def test_get_low_hours_single_pattern():
    tracker = Tracker()
    tracker.daily_patterns = {
        0: [3.0]
    }
    result = tracker.get_low_hours(bottom_n=1)
    assert result == [(0, 3.0)]