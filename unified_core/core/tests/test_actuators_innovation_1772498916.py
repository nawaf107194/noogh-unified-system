import pytest
from unittest.mock import Mock, patch

class MockActuator:
    def __init__(self):
        self.filesystem = Mock()
        self.network = Mock()
        self.process = Mock()

    def get_resilience_metrics(self):
        return {
            "blocked_count": 0,
            "rejection_count": 0,
            "cooldown_count": 0
        }

def test_get_stats_happy_path():
    actuator = MockActuator()
    expected_output = {
        "filesystem": {"blocked_count": 0, "rejection_count": 0, "cooldown_count": 0},
        "network": {"blocked_count": 0, "rejection_count": 0, "cooldown_count": 0},
        "process": {"blocked_count": 0, "rejection_count": 0, "cooldown_count": 0},
        "summary": {
            "blocked_total": 0,
            "rejections_total": 0,
            "cooldowns_total": 0
        }
    }
    assert actuator.get_stats() == expected_output

def test_get_stats_edge_case_empty_metrics():
    actuator = MockActuator()
    actuator.filesystem.get_resilience_metrics.return_value = {}
    actuator.network.get_resilience_metrics.return_value = {}
    actuator.process.get_resilience_metrics.return_value = {}
    expected_output = {
        "filesystem": {},
        "network": {},
        "process": {},
        "summary": {
            "blocked_total": 0,
            "rejections_total": 0,
            "cooldowns_total": 0
        }
    }
    assert actuator.get_stats() == expected_output

def test_get_stats_edge_case_none_metrics():
    actuator = MockActuator()
    actuator.filesystem.get_resilience_metrics.return_value = None
    actuator.network.get_resilience_metrics.return_value = None
    actuator.process.get_resilience_metrics.return_value = None
    expected_output = {
        "filesystem": {},
        "network": {},
        "process": {},
        "summary": {
            "blocked_total": 0,
            "rejections_total": 0,
            "cooldowns_total": 0
        }
    }
    assert actuator.get_stats() == expected_output

def test_get_stats_edge_case_boundary_metrics():
    actuator = MockActuator()
    actuator.filesystem.get_resilience_metrics.return_value = {
        "blocked_count": 1,
        "rejection_count": 2,
        "cooldown_count": 3
    }
    actuator.network.get_resilience_metrics.return_value = {
        "blocked_count": 4,
        "rejection_count": 5,
        "cooldown_count": 6
    }
    actuator.process.get_resilience_metrics.return_value = {
        "blocked_count": 7,
        "rejection_count": 8,
        "cooldown_count": 9
    }
    expected_output = {
        "filesystem": {"blocked_count": 1, "rejection_count": 2, "cooldown_count": 3},
        "network": {"blocked_count": 4, "rejection_count": 5, "cooldown_count": 6},
        "process": {"blocked_count": 7, "rejection_count": 8, "cooldown_count": 9},
        "summary": {
            "blocked_total": 12,
            "rejections_total": 15,
            "cooldowns_total": 18
        }
    }
    assert actuator.get_stats() == expected_output

def test_get_stats_error_case_invalid_input():
    with pytest.raises(TypeError):
        actuator = MockActuator()
        actuator.filesystem.get_resilience_metrics.return_value = "invalid"
        actuator.network.get_resilience_metrics.return_value = "invalid"
        actuator.process.get_resilience_metrics.return_value = "invalid"
        actuator.get_stats()