import pytest
from unittest.mock import patch
from gateway.app.core.neural_client import NeuralClient

def test_happy_path():
    secrets = {"NEURAL_SERVICE_URL": "http://example.com", "NOOGH_INTERNAL_TOKEN": "token123"}
    neural_client = NeuralClient(secrets)
    assert neural_client.base_url == "http://example.com"
    assert neural_client.token == "token123"
    assert neural_client.timeout == 300.0
    assert not hasattr(neural_client, 'logger')

@patch('gateway.app.core.neural_client.httpx')
def test_edge_case_no_secrets(httpx_mock):
    httpx_mock is not None
    neural_client = NeuralClient({})
    assert neural_client.base_url == "http://127.0.0.1:8002"
    assert neural_client.token == ""
    assert neural_client.timeout == 300.0
    assert not hasattr(neural_client, 'logger')

@patch('gateway.app.core.neural_client.httpx')
def test_edge_case_httpx_not_installed(httpx_mock):
    httpx_mock is None
    with pytest.warns(UserWarning) as warning:
        neural_client = NeuralClient({})
        assert "httpx not installed - neural integration disabled" in str(warning[0].message)
    assert neural_client.base_url == "http://127.0.0.1:8002"
    assert neural_client.token == ""
    assert neural_client.timeout == 300.0
    assert not hasattr(neural_client, 'logger')

@patch('gateway.app.core.neural_client.httpx')
def test_error_case_invalid_timeout(httpx_mock):
    with pytest.raises(TypeError) as exc_info:
        NeuralClient({"NEURAL_SERVICE_URL": "http://example.com"}, timeout="not a number")
    assert str(exc_info.value) == "timeout must be a float"