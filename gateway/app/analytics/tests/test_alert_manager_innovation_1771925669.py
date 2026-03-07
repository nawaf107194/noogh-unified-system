import pytest
from typing import List, Dict, Any

class MockAlertManager:
    def __init__(self):
        self._lock = object()
        self._alerts = [
            {"id": 1, "message": "Alert 1"},
            {"id": 2, "message": "Alert 2"},
            # ... more alerts ...
        ]

    def list_alerts(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._lock:
            return self._alerts[-limit:]

@pytest.fixture
def alert_manager():
    return MockAlertManager()

def test_happy_path(alert_manager):
    result = alert_manager.list_alerts()
    assert len(result) == 200
    assert all(isinstance(alert, dict) for alert in result)

def test_edge_case_empty_list(alert_manager):
    alert_manager._alerts = []
    result = alert_manager.list_alerts(limit=10)
    assert result == []

def test_edge_case_none_limit(alert_manager):
    result = alert_manager.list_alerts(None)
    assert result == alert_manager._alerts[-200:]

def test_boundary_case_limit_zero(alert_manager):
    result = alert_manager.list_alerts(limit=0)
    assert result == []

def test_boundary_case_exact_limit(alert_manager):
    limit = len(alert_manager._alerts)
    result = alert_manager.list_alerts(limit=limit)
    assert result == alert_manager._alerts

def test_boundary_case_greater_than_count(alert_manager):
    result = alert_manager.list_alerts(limit=300)
    assert result == alert_manager._alerts

def test_error_case_negative_limit(alert_manager):
    with pytest.raises(ValueError):
        alert_manager.list_alerts(limit=-1)

def test_async_behavior_is_not_applicable():
    # Since the function does not involve asynchronous operations, this case is not applicable
    pass