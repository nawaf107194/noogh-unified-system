import pytest
from unittest.mock import patch, MagicMock
import time

class MockGatewayClient:
    def __init__(self):
        self.completed_tasks = []

    def get_completed_tasks(self):
        return self.completed_tasks

@pytest.fixture
def multi_agent():
    return MultiAgent(MockGatewayClient())

def test_retrieve_results_happy_path(multi_agent):
    # Setupmock to return some completed tasks
    multi_agent.gateway_client.completed_tasks = [
        {'result': 'Task 1 Result'},
        {'result': 'Task 2 Result'}
    ]
    
    results = multi_agent.retrieve_results()
    assert results == ['Task 1 Result', 'Task 2 Result']

def test_retrieve_results_empty(multi_agent):
    # Setupmock to return no completed tasks
    multi_agent.gateway_client.completed_tasks = []
    
    results = multi_agent.retrieve_results()
    assert results == []

def test_retrieve_results_with_sleep_no_task(multi_agent):
    with patch('time.sleep') as mock_sleep:
        # Setupmock to return some completed tasks after the first call
        multi_agent.gateway_client.completed_tasks = [{'result': 'Task Result'}]
        
        results = multi_agent.retrieve_results()
        assert results == ['Task Result']
        mock_sleep.assert_called_once()

def test_retrieve_results_with_exception(multi_agent):
    # Setupmock to raise an exception when called
    with patch.object(multi_agent.gateway_client, 'get_completed_tasks', side_effect=Exception('Gateway Error')):
        with pytest.raises(Exception) as exc_info:
            multi_agent.retrieve_results()
        
        assert str(exc_info.value) == 'Gateway Error'