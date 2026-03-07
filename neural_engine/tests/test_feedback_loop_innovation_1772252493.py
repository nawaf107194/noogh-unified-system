import pytest
from datetime import datetime, timedelta
from neural_engine.feedback_loop import FeedbackLoop

class MockMetric:
    def __init__(self, timestamp=None, success=True, duration=1.0):
        self.timestamp = timestamp if timestamp else datetime.now()
        self.success = success
        self.duration = duration

@pytest.fixture
def feedback_loop():
    return FeedbackLoop()

def test_get_recent_performance_happy_path(feedback_loop):
    # Arrange
    now = datetime.now()
    metrics = [
        MockMetric(now - timedelta(minutes=10), True, 2.0),
        MockMetric(now - timedelta(minutes=5), False, 3.0),
        MockMetric(now - timedelta(minutes=3), True, 1.5)
    ]
    feedback_loop.metrics.extend(metrics)

    # Act
    result = feedback_loop.get_recent_performance()

    # Assert
    assert result == {
        "count": 3,
        "successful": 2,
        "failed": 1,
        "success_rate": (2 / 3) * 100,
        "avg_duration": (2.0 + 3.0 + 1.5) / 3
    }

def test_get_recent_performance_empty_metrics(feedback_loop):
    # Arrange

    # Act
    result = feedback_loop.get_recent_performance()

    # Assert
    assert result == {
        "count": 0,
        "successful": 0,
        "failed": 0,
        "success_rate": 0.0,
        "avg_duration": 0.0
    }

def test_get_recent_performance_with_old_metrics(feedback_loop):
    # Arrange
    now = datetime.now()
    metrics = [
        MockMetric(now - timedelta(minutes=70), True, 2.0),
        MockMetric(now - timedelta(minutes=65), False, 3.0)
    ]
    feedback_loop.metrics.extend(metrics)

    # Act
    result = feedback_loop.get_recent_performance()

    # Assert
    assert result == {
        "count": 0,
        "successful": 0,
        "failed": 0,
        "success_rate": 0.0,
        "avg_duration": 0.0
    }

def test_get_recent_performance_with_none_minutes(feedback_loop):
    # Arrange

    # Act
    result = feedback_loop.get_recent_performance(None)

    # Assert
    assert result == {
        "count": 0,
        "successful": 0,
        "failed": 0,
        "success_rate": 0.0,
        "avg_duration": 0.0
    }

def test_get_recent_performance_with_negative_minutes(feedback_loop):
    # Arrange

    # Act
    result = feedback_loop.get_recent_performance(-10)

    # Assert
    assert result == {
        "count": 0,
        "successful": 0,
        "failed": 0,
        "success_rate": 0.0,
        "avg_duration": 0.0
    }

def test_get_recent_performance_with_float_minutes(feedback_loop):
    # Arrange

    # Act
    result = feedback_loop.get_recent_performance(30.5)

    # Assert
    assert result == {
        "count": 0,
        "successful": 0,
        "failed": 0,
        "success_rate": 0.0,
        "avg_duration": 0.0
    }

def test_get_recent_performance_with_large_minutes(feedback_loop):
    # Arrange

    # Act
    result = feedback_loop.get_recent_performance(120)

    # Assert
    assert result == {
        "count": 0,
        "successful": 0,
        "failed": 0,
        "success_rate": 0.0,
        "avg_duration": 0.0
    }