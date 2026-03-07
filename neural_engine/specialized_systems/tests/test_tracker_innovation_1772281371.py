import pytest

class MockTracker:
    def __init__(self):
        self.daily_patterns = {
            0: [10, 20, 30],
            1: [5, 15, 25],
            2: [10, 10, 10],
            # Add more hours as needed for testing
        }

    def get_energy_curve(self) -> Dict[int, float]:
        return {hour: sum(levels) / len(levels) for hour, levels in self.daily_patterns.items()}

def test_get_energy_curve_happy_path():
    tracker = MockTracker()
    result = tracker.get_energy_curve()
    expected = {
        0: 20.0,
        1: 15.0,
        2: 10.0,
        # Add more hours as needed for testing
    }
    assert result == expected

def test_get_energy_curve_empty_input():
    tracker = MockTracker()
    tracker.daily_patterns = {}
    result = tracker.get_energy_curve()
    assert result == {}

def test_get_energy_curve_none_input():
    tracker = MockTracker()
    tracker.daily_patterns = None
    result = tracker.get_energy_curve()
    assert result is None

def test_get_energy_curve_boundary_hours():
    tracker = MockTracker()
    tracker.daily_patterns = {
        23: [5, 10, 15],
        0: [10, 20, 30],
    }
    result = tracker.get_energy_curve()
    expected = {
        23: 10.0,
        0: 20.0,
    }
    assert result == expected

def test_get_energy_curve_invalid_input():
    tracker = MockTracker()
    tracker.daily_patterns = "not a dictionary"
    result = tracker.get_energy_curve()
    assert result is None