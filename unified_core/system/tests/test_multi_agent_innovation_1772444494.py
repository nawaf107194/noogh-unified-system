import pytest
from unittest.mock import patch, MagicMock
import time

class MockGatewayClient:
    def get_active_tasks(self):
        return ["task1", "task2"]

@pytest.fixture
def manager():
    class Manager:
        def __init__(self):
            self.gateway_client = MockGatewayClient()
    return Manager()

@patch('time.sleep')
def test_manage_agents_happy_path(mock_sleep, manager):
    with patch.object(manager, 'gateway_client') as mock_client:
        mock_client.get_active_tasks.return_value = ["task1", "task2"]
        
        manager.manage_agents()
        
        assert mock_client.get_active_tasks.call_count >= 1
        mock_sleep.assert_called_once_with(1)

@patch('time.sleep')
def test_manage_agents_empty_task_list(mock_sleep, manager):
    with patch.object(manager, 'gateway_client') as mock_client:
        mock_client.get_active_tasks.return_value = []
        
        manager.manage_agents()
        
        assert mock_client.get_active_tasks.call_count >= 1
        mock_sleep.assert_called_once_with(1)

@patch('time.sleep')
def test_manage_agents_none_task_list(mock_sleep, manager):
    with patch.object(manager, 'gateway_client') as mock_client:
        mock_client.get_active_tasks.return_value = None
        
        manager.manage_agents()
        
        assert mock_client.get_active_tasks.call_count >= 1
        mock_sleep.assert_called_once_with(1)

@patch('time.sleep')
def test_manage_agents_error_case(mock_sleep, manager):
    with patch.object(manager, 'gateway_client') as mock_client:
        mock_client.get_active_tasks.side_effect = Exception("An error occurred")
        
        with pytest.raises(Exception) as exc_info:
            manager.manage_agents()
        
        assert str(exc_info.value) == "An error occurred"
        mock_client.get_active_tasks.assert_called_once_with()
        mock_sleep.assert_not_called()

@patch('time.sleep')
def test_manage_agents_async_behavior(mock_sleep, manager):
    with patch.object(manager, 'gateway_client') as mock_client:
        mock_client.get_active_tasks.return_value = ["task1"]
        
        import threading
        def run_manager():
            manager.manage_agents()
        
        thread = threading.Thread(target=run_manager)
        thread.start()
        time.sleep(0.5)  # Allow some time for the thread to start
        mock_client.get_active_tasks.assert_called_once_with()
        mock_sleep.assert_called_once_with(1)
        thread.join()