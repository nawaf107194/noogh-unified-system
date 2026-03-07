import os
from unittest.mock import patch
from gateway.app.security.secrets_manager import load, SecretsManagerError

def test_load_happy_path():
    with patch.dict(os.environ, {'REQUIRED_KEY': 'value1', 'OPTIONAL_KEY': 'value2'}):
        result = load()
        assert result == {'REQUIRED_KEY': 'value1', 'OPTIONAL_KEY': 'value2'}

def test_load_missing_required_key():
    with patch.dict(os.environ, {'OPTIONAL_KEY': 'value2'}):
        with pytest.raises(SecretsManagerError) as exc_info:
            load()
        assert "CRITICAL: Missing required environment variables" in str(exc_info.value)

def test_load_missing_optional_key():
    with patch.dict(os.environ, {'REQUIRED_KEY': 'value1'}):
        result = load()
        assert result == {'REQUIRED_KEY': 'value1'}

def test_load_all_keys_empty():
    with patch.dict(os.environ, {}):
        with pytest.raises(SecretsManagerError) as exc_info:
            load()
        assert "CRITICAL: Missing required environment variables: REQUIRED_KEY" in str(exc_info.value)

def test_load_all_keys_none():
    with patch.dict(os.environ, {'REQUIRED_KEY': None, 'OPTIONAL_KEY': None}):
        with pytest.raises(SecretsManagerError) as exc_info:
            load()
        assert "CRITICAL: Missing required environment variables: REQUIRED_KEY" in str(exc_info.value)