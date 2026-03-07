import pytest
from unittest.mock import Mock

class TestAlertManager:
    @pytest.fixture
    def alert_manager(self):
        class MockAlertManager:
            _lock = Mock()
            _alerts = []
            
            def list_alerts(self, limit: int = 200) -> List[Dict[str, Any]]:
                with self._lock:
                    return self._alerts[-limit:]
        
        return MockAlertManager()

    def test_happy_path(self, alert_manager):
        alert_manager._alerts = [{'id': 1, 'message': 'Test Alert'}]
        result = alert_manager.list_alerts()
        assert len(result) == 1
        assert result[0] == {'id': 1, 'message': 'Test Alert'}

    def test_edge_case_empty(self, alert_manager):
        result = alert_manager.list_alerts()
        assert len(result) == 0

    def test_edge_case_boundary(self, alert_manager):
        alert_manager._alerts = [{'id': i, 'message': f'Test Alert {i}'} for i in range(250)]
        result = alert_manager.list_alerts(limit=10)
        assert len(result) == 10
        assert result[0] == {'id': 240, 'message': 'Test Alert 240'}
        assert result[-1] == {'id': 249, 'message': 'Test Alert 249'}

    def test_invalid_input_limit_negative(self, alert_manager):
        with pytest.raises(ValueError) as exc_info:
            alert_manager.list_alerts(limit=-1)
        assert str(exc_info.value) == "Limit must be a non-negative integer"

    def test_invalid_input_limit_not_integer(self, alert_manager):
        with pytest.raises(TypeError) as exc_info:
            alert_manager.list_alerts(limit='200')
        assert str(exc_info.value) == "Limit must be a non-negative integer"