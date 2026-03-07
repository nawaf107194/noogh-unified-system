import pytest
from typing import Dict, Any

class Tracker:
    def __init__(self):
        self.energy_logs = []
        self.daily_patterns = []

    def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics"""
        return {
            "total_logs": len(self.energy_logs),
            "hours_tracked": len(self.daily_patterns),
            "avg_logs_per_hour": (len(self.energy_logs) / len(self.daily_patterns) if self.daily_patterns else 0),
        }

@pytest.fixture
def tracker():
    return Tracker()

def test_get_stats_happy_path(tracker):
    # Arrange
    tracker.energy_logs = [1, 2, 3, 4]
    tracker.daily_patterns = ['Mon', 'Tue', 'Wed']

    # Act
    result = tracker.get_stats()

    # Assert
    assert result == {
        "total_logs": 4,
        "hours_tracked": 3,
        "avg_logs_per_hour": pytest.approx(1.3333),
    }

def test_get_stats_empty_daily_patterns(tracker):
    # Arrange
    tracker.energy_logs = [1, 2, 3, 4]
    tracker.daily_patterns = []

    # Act
    result = tracker.get_stats()

    # Assert
    assert result == {
        "total_logs": 4,
        "hours_tracked": 0,
        "avg_logs_per_hour": 0.0,
    }

def test_get_stats_empty_energy_logs(tracker):
    # Arrange
    tracker.energy_logs = []
    tracker.daily_patterns = ['Mon', 'Tue', 'Wed']

    # Act
    result = tracker.get_stats()

    # Assert
    assert result == {
        "total_logs": 0,
        "hours_tracked": 3,
        "avg_logs_per_hour": 0.0,
    }

def test_get_stats_empty_both(tracker):
    # Arrange
    tracker.energy_logs = []
    tracker.daily_patterns = []

    # Act
    result = tracker.get_stats()

    # Assert
    assert result == {
        "total_logs": 0,
        "hours_tracked": 0,
        "avg_logs_per_hour": 0.0,
    }