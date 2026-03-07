import pytest
from datetime import datetime, timedelta
from collections import defaultdict

class MockErrorHistory:
    def __init__(self):
        self.error_history = []

    def get_error_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get error trends over time"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_history if e.timestamp > cutoff]

        error_counts = defaultdict(int)
        for error in recent_errors:
            error_counts[error.error_type] += 1

        return {
            "total_errors": len(recent_errors),
            "unique_error_types": len(error_counts),
            "error_breakdown": dict(error_counts),
        }

class ErrorLogEntry:
    def __init__(self, timestamp: datetime, error_type: str):
        self.timestamp = timestamp
        self.error_type = error_type

@pytest.fixture
def mock_error_history():
    return MockErrorHistory()

def test_happy_path(mock_error_history):
    # Add some sample data to the history
    mock_error_history.error_history.append(ErrorLogEntry(datetime.now() - timedelta(hours=1), "TypeError"))
    mock_error_history.error_history.append(ErrorLogEntry(datetime.now() - timedelta(hours=1), "ValueError"))

    result = mock_error_history.get_error_trends()

    assert result["total_errors"] == 2
    assert result["unique_error_types"] == 2
    assert result["error_breakdown"]["TypeError"] == 1
    assert result["error_breakdown"]["ValueError"] == 1

def test_edge_case_empty(mock_error_history):
    result = mock_error_history.get_error_trends()

    assert result["total_errors"] == 0
    assert result["unique_error_types"] == 0
    assert result["error_breakdown"] == {}

def test_edge_case_boundary(mock_error_history):
    # Add an error exactly at the boundary
    mock_error_history.error_history.append(ErrorLogEntry(datetime.now() - timedelta(hours=24), "TimeoutError"))

    result = mock_error_history.get_error_trends()

    assert result["total_errors"] == 0
    assert result["unique_error_types"] == 0
    assert result["error_breakdown"] == {}

def test_error_case_negative_hours(mock_error_history):
    # This should not raise an error, as the function has a default value for hours
    result = mock_error_history.get_error_trends(hours=-1)

    assert result["total_errors"] == 0
    assert result["unique_error_types"] == 0
    assert result["error_breakdown"] == {}

def test_error_case_non_integer_hours(mock_error_history):
    # This should not raise an error, as the function has a default value for hours
    result = mock_error_history.get_error_trends(hours="24")

    assert result["total_errors"] == 0
    assert result["unique_error_types"] == 0
    assert result["error_breakdown"] == {}