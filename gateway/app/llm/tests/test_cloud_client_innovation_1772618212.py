import pytest
from httpx import Client
from typing import Dict
from src.gateway.app.llm.cloud_client import CloudClient
from src.gateway.app.llm.settings import get_settings

def test_cloud_client_init_happy_path():
    # Test with normal inputs
    secrets = {"key1": "value1", "key2": "value2"}
    client = CloudClient(secrets)
    
    # Verify settings are loaded
    assert client.settings == get_settings()
    
    # Verify secrets are stored correctly
    assert client.secrets == secrets
    
    # Verify HTTP client is initialized
    assert isinstance(client.client, Client)
    assert client.client.timeout == 120.0

def test_cloud_client_init_empty_secrets():
    # Test with empty dictionary
    secrets = {}
    client = CloudClient(secrets)
    
    # Verify empty secrets are handled
    assert client.secrets == {}

def test_cloud_client_init_with_none_secrets():
    # Test with None input
    with pytest.raises(TypeError):
        CloudClient(None)

def test_cloud_client_init_with_invalid_type():
    # Test with invalid type (not dict)
    with pytest.raises(TypeError):
        CloudClient(["invalid", "secrets"])