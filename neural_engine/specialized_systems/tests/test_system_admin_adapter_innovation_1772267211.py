import pytest

from neural_engine.specialized_systems.system_admin_adapter import SystemAdminAdapter

@pytest.fixture
def adapter():
    return SystemAdminAdapter()

def test_analyze_trends_happy_path(adapter):
    adapter.observation_history = [
        {"cpu": {"cpu_usage_percent": 50}},
        {"cpu": {"cpu_usage_percent": 60}},
        {"cpu": {"cpu_usage_percent": 70}},
        {"mem": {"percent": 30}}
    ]
    result = adapter.analyze_trends()
    assert result == {
        "window_size": 4,
        "cpu_trend": "increasing",
        "cpu_current": 70,
        "memory_trend": "stable",
        "memory_current": 30
    }

def test_analyze_trends_empty_history(adapter):
    adapter.observation_history = []
    result = adapter.analyze_trends()
    assert result == {
        "status": "insufficient_data"
    }

def test_analyze_trends_single_observation(adapter):
    adapter.observation_history = [{"cpu": {"cpu_usage_percent": 50}}]
    result = adapter.analyze_trends()
    assert result == {
        "window_size": 1,
        "cpu_trend": "stable",
        "cpu_current": 50,
        "memory_trend": "stable",
        "memory_current": 0
    }

def test_analyze_trends_boundary_window(adapter):
    adapter.observation_history = [
        {"cpu": {"cpu_usage_percent": 50}},
        {"cpu": {"cpu_usage_percent": 60}},
        {"cpu": {"cpu_usage_percent": 70}},
        {"mem": {"percent": 30}}
    ]
    result = adapter.analyze_trends(window_minutes=2)
    assert result == {
        "window_size": 2,
        "cpu_trend": "stable",
        "cpu_current": 70,
        "memory_trend": "stable",
        "memory_current": 30
    }

def test_analyze_trends_no_memory_data(adapter):
    adapter.observation_history = [
        {"cpu": {"cpu_usage_percent": 50}},
        {"cpu": {"cpu_usage_percent": 60}},
        {"cpu": {"cpu_usage_percent": 70}}
    ]
    result = adapter.analyze_trends()
    assert result == {
        "window_size": 3,
        "cpu_trend": "increasing",
        "cpu_current": 70,
        "memory_trend": "stable",
        "memory_current": 0
    }