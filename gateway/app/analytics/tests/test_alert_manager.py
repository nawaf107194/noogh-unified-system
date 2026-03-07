import pytest
from unittest.mock import patch, MagicMock
from gateway.app.analytics.alert_manager import get_alert_manager, AlertManager

@pytest.fixture
def mock_alert_manager():
    with patch('gateway.app.analytics.alert_manager.AlertManager', autospec=True) as MockAlertManager:
        yield MockAlertManager()

def test_happy_path(mock_alert_manager):
    # Ensure the first call initializes the manager
    assert get_alert_manager() == mock_alert_manager
    # Subsequent calls should return the same instance
    assert get_alert_manager() == mock_alert_manager

def test_edge_cases():
    # Since there are no parameters to pass, edge cases like empty or None do not apply here.
    # This function should behave the same way regardless of external state.
    pass

def test_error_cases():
    # There are no error cases since the function does not take any parameters and does not perform validation.
    pass

def test_async_behavior():
    # The provided function does not involve async operations, so no test is needed for async behavior.
    pass