import pytest
from unittest.mock import patch
from gateway.app.core.neural_client import NeuralClient

def test_happy_path():
    secrets = {
        "NEURAL_SERVICE_URL": "http://example.com",
        "NOOGH_INTERNAL_TOKEN": "token123"
    }
    client = NeuralClient(secrets)
    assert client.base_url == "http://example.com"
    assert client.token == "token123"
    assert client.timeout == 300.0

def test_edge_case_empty_secrets():
    secrets = {}
    client = NeuralClient(secrets)
    assert client.base_url == "http://127.0.0.1:8002"
    assert client.token == ""
    assert client.timeout == 300.0

def test_edge_case_none_secrets():
    with patch.dict('os.environ', {}, clear=True):
        client = NeuralClient(None)
        assert client.base_url == "http://127.0.0.1:8002"
        assert client.token == ""
        assert client.timeout == 300.0

def test_boundary_case_timeout_zero():
    secrets = {
        "NEURAL_SERVICE_URL": "http://example.com",
        "NOOGH_INTERNAL_TOKEN": "token123"
    }
    client = NeuralClient(secrets, timeout=0.0)
    assert client.base_url == "http://example.com"
    assert client.token == "token123"
    assert client.timeout == 0.0

def test_boundary_case_timeout_negative():
    secrets = {
        "NEURAL_SERVICE_URL": "http://example.com",
        "NOOGH_INTERNAL_TOKEN": "token123"
    }
    client = NeuralClient(secrets, timeout=-1.0)
    assert client.base_url == "http://example.com"
    assert client.token == "token123"
    assert client.timeout == 300.0

def test_async_behavior():
    with patch('gateway.app.core.neural_client.httpx') as mock_httpx:
        secrets = {
            "NEURAL_SERVICE_URL": "http://example.com",
            "NOOGH_INTERNAL_TOKEN": "token123"
        }
        client = NeuralClient(secrets)
        assert client.base_url == "http://example.com"
        assert client.token == "token123"
        assert client.timeout == 300.0
        mock_httpx.assert_called_once()