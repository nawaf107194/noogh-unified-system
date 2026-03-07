import pytest
from unittest.mock import patch
from gateway.app.analytics.ws_ingestor import WSIngestor
from gateway.app.constants import PORTS

@pytest.fixture
def ingestor_instance():
    return WSIngestor()

def test_happy_path(ingestor_instance):
    assert ingestor_instance.poll_interval == 2.0
    assert ingestor_instance.running is False
    assert ingestor_instance._task is None
    assert isinstance(ingestor_instance._seen, set)
    assert len(ingestor_instance._seen) == 0
    assert ingestor_instance._seen_max == 2000
    assert ingestor_instance.neural_events_url.endswith("/api/v1/autonomic/events")

def test_edge_cases():
    with patch('os.getenv', return_value=None):
        instance = WSIngestor()
        assert instance.neural_events_url == f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}/api/v1/autonomic/events"
    
    with patch('os.getenv', return_value=""):
        instance = WSIngestor()
        assert instance.nevironmental_events_url == f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}/api/v1/autonomic/events"

def test_error_cases():
    with pytest.raises(ValueError):
        WSIngestor(poll_interval=-1.0)  # Negative interval should raise an error
    
    with pytest.raises(TypeError):
        WSIngestor(poll_interval="not a float")  # Non-float interval should raise an error

@patch('gateway.app.analytics.ws_ingestor.asyncio')
def test_async_behavior(mock_asyncio, ingestor_instance):
    ingestor_instance.start()
    mock_asyncio.create_task.assert_called_once()
    assert ingestor_instance._task is not None
    assert ingestor_instance.running is True