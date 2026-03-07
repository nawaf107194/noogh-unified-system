import pytest
from gateway.app.analytics.alert_manager import AlertManager

class TestAlertManager:

    @pytest.fixture
    def alert_manager(self):
        return AlertManager()

    def test_clear_alerts_happy_path(self, alert_manager):
        # Add some alerts to the manager
        alert_manager._alerts = {'alert1': True, 'alert2': False}
        
        # Call the clear_alerts method
        alert_manager.clear_alerts()
        
        # Assert that the alerts are cleared
        assert not alert_manager._alerts

    def test_clear_alerts_edge_case_empty(self, alert_manager):
        # Call clear_alerts when there are no alerts
        alert_manager.clear_alerts()
        
        # Assert that the alerts remain empty
        assert not alert_manager._alerts

    def test_clear_alerts_edge_case_none(self, alert_manager):
        # Set _alerts to None
        alert_manager._alerts = None
        
        # Call clear_alerts when _alerts is None
        alert_manager.clear_alerts()
        
        # Assert that _alerts becomes an empty dictionary
        assert alert_manager._alerts == {}

    def test_clear_alerts_async_behavior(self, alert_manager):
        import asyncio

        async def add_and_clear_alerts():
            alert_manager._alerts = {'alert1': True}
            await asyncio.sleep(0.1)  # Simulate some time passing
            alert_manager.clear_alerts()
        
        # Run the coroutine and wait for it to complete
        asyncio.run(add_and_clear_alerts())
        
        # Assert that the alerts are cleared
        assert not alert_manager._alerts