import pytest

from neural_engine.specialized_systems.tracker import Tracker

def test_get_energy_curve_happy_path():
    tracker = Tracker()
    tracker.daily_patterns = {
        0: [1.2, 1.4, 1.3],
        1: [2.5, 2.6, 2.7],
        2: [0.8, 0.9, 0.7]
    }
    expected_output = {
        0: 1.3,
        1: 2.6,
        2: 0.8
    }
    assert tracker.get_energy_curve() == expected_output

def test_get_energy_curve_empty_input():
    tracker = Tracker()
    tracker.daily_patterns = {}
    expected_output = {}
    assert tracker.get_energy_curve() == expected_output

def test_get_energy_curve_none_input():
    tracker = Tracker()
    tracker.daily_patterns = None
    assert tracker.get_energy_curve() is None

def test_get_energy_curve_boundary_values():
    tracker = Tracker()
    tracker.daily_patterns = {
        23: [5.0, 5.1],
        0: [1.0]
    }
    expected_output = {
        23: 5.05,
        0: 1.0
    }
    assert tracker.get_energy_curve() == expected_output

def test_get_energy_curve_invalid_input():
    tracker = Tracker()
    with pytest.raises(TypeError):
        tracker.daily_patterns = "invalid_input"
        tracker.get_energy_curve()