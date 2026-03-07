import pytest
from unittest.mock import patch, MagicMock
from aiohttp import ClientSession
from collections import OrderedDict
import os

from unified_core.neural_bridge import NeuralEngineClient
from unified_core.circuit_breaker import CircuitBreaker
from unified_core.config import config

# Mock environment variables for testing
os.environ = {
    "NEURAL_ENGINE_URL": "http://test-url:8002",
    "NEURAL_ENGINE_MODE": "local",
    "NEURAL_TIMEOUT_SECONDS": "120",
    "VLLM_MODEL_NAME": "test-model",
    "VLLM_MAX_TOKENS": "2048",
    "VLLM_CONTEXT_LENGTH": "2048",
    "VLLM_TEMPERATURE": "0.7",
    "NEURAL_MAX_RETRIES": "3",
    "CB_FAILURE_THRESHOLD": "5",
    "CB_RECOVERY_TIMEOUT": "10"
}

@pytest.mark.asyncio
async def test_init_happy_path():
    client = NeuralEngineClient()
    assert client._base_url == "http://test-url:8002"
    assert client._mode == "local"
    assert client._timeout.total == 120
    assert client._vllm_model == "test-model"
    assert client._vllm_max_tokens == 2048
    assert client._vllm_context_length == 2048
    assert client._vllm_temperature == 0.7
    assert client._max_retries == 3
    assert isinstance(client._circuit_breaker, CircuitBreaker)
    assert client._cache is not None

@pytest.mark.asyncio
async def test_init_empty_base_url():
    client = NeuralEngineClient(base_url="")
    assert client._base_url == "http://127.0.0.1:8002"

@pytest.mark.asyncio
async def test_init_none_mode():
    client = NeuralEngineClient(mode=None)
    assert client._mode == "local"

@pytest.mark.asyncio
async def test_init_edge_cases():
    client = NeuralEngineClient(base_url="  ", mode="vllm")
    assert client._base_url == "http://127.0.0.1:8002"
    assert client._timeout.total == 600

@pytest.mark.asyncio
async def test_init_invalid_mode():
    with pytest.raises(ValueError) as exc_info:
        NeuralEngineClient(mode="invalid")
    assert str(exc_info.value) == "Invalid mode: invalid"

# Test async behavior (if applicable)
@pytest.mark.asyncio
async def test_async_behavior(mocker):
    with patch("aiohttp.ClientSession") as mock_session:
        client = NeuralEngineClient()
        await client._get_client_session()
        mock_session.assert_called_once_with(base_url="http://test-url:8002", timeout=aiohttp.ClientTimeout(total=120))