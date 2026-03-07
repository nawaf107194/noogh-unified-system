import pytest
from unittest.mock import patch, mock_open

from gateway.app.core.neural_client import NeuralClient
import httpx

def test_init_happy_path():
    secrets = {
        "NEURAL_SERVICE_URL": "http://neural.example.com",
        "NOOGH_INTERNAL_TOKEN": "abc123"
    }
    client = NeuralClient(secrets)
    
    assert client.base_url == "http://neural.example.com"
    assert client.token == "abc123"
    assert client.timeout == 300.0

def test_init_empty_secrets():
    secrets = {}
    client = NeuralClient(secrets)
    
    assert client.base_url == "http://127.0.0.1:8002"
    assert client.token == ""
    assert client.timeout == 300.0

def test_init_none_secrets():
    client = NeuralClient(None)
    
    assert client.base_url == "http://127.0.0.1:8002"
    assert client.token == ""
    assert client.timeout == 300.0

def test_init_boundary_timeout():
    secrets = {
        "NEURAL_SERVICE_URL": "http://neural.example.com",
        "NOOGH_INTERNAL_TOKEN": "abc123"
    }
    client = NeuralClient(secrets, timeout=0)
    
    assert client.base_url == "http://neural.example.com"
    assert client.token == "abc123"
    assert client.timeout == 0

def test_init_invalid_timeout():
    secrets = {
        "NEURAL_SERVICE_URL": "http://neural.example.com",
        "NOOGH_INTERNAL_TOKEN": "abc123"
    }
    
    with pytest.raises(ValueError):
        NeuralClient(secrets, timeout="not a number")

@patch('gateway.app.core.neural_client.httpx')
def test_init_httpx_not_installed(mock_httpx):
    mock_open_side_effect = OSError()
    with patch('builtins.open', mock_open_side_effect=mock_open_side_effect):
        client = NeuralClient(None)
        
        assert client.base_url == "http://127.0.0.1:8002"
        assert client.token == ""
        assert client.timeout == 300.0
        mock_httpx.is_installed.assert_called_once()