import pytest
from unittest.mock import patch, MagicMock
import requests
import time

@pytest.fixture
def mock_requests_get():
    with patch('requests.get', new_callable=MagicMock) as mock_get:
        yield mock_get

@pytest.mark.parametrize("url, name, expected_output", [
    ("http://example.com", "Example Service", True),  # Happy path
    ("http://example.com", "Example Service", False),  # Service not ready
])
def test_wait_http_happy_path(mock_requests_get, url, name, expected_output):
    if expected_output:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response
    else:
        mock_requests_get.side_effect = requests.exceptions.RequestException
    
    result = wait_http(url, name)
    assert result == expected_output

def test_wait_http_edge_cases():
    with pytest.raises(ValueError):
        wait_http("", "Empty URL", 15)  # Empty URL should raise ValueError
    with pytest.raises(TypeError):
        wait_http(None, "None URL", 15)  # None URL should raise TypeError
    with pytest.raises(ValueError):
        wait_http("http://example.com", "", 15)  # Empty name should raise ValueError
    with pytest.raises(ValueError):
        wait_http("http://example.com", None, 15)  # None name should raise ValueError
    with pytest.raises(ValueError):
        wait_http("http://example.com", "Service", -1)  # Negative timeout should raise ValueError

def test_wait_http_error_cases(mock_requests_get):
    mock_requests_get.side_effect = requests.exceptions.RequestException
    result = wait_http("http://example.com", "Error Service")
    assert result is False

def test_wait_http_async_behavior():
    # Since the function does not use async/await, we can simulate the behavior
    # by using a mock that sleeps and then returns.
    with patch('time.sleep', return_value=None):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_get.side_effect = [requests.exceptions.RequestException] * 14 + [mock_response]
        result = wait_http("http://example.com", "Async Service")
        assert result is True