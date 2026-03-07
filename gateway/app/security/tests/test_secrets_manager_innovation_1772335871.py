import os
from unittest.mock import patch
from gateway.app.security.secrets_manager import SecretsManager, SecretsManagerError

def test_load_happy_path():
    with patch.dict(os.environ, {'SECRET_KEY': 'value1', 'DATABASE_URL': 'value2'}):
        result = SecretsManager.load()
    assert result == {'SECRET_KEY': 'value1', 'DATABASE_URL': 'value2'}

def test_load_missing_required_key():
    with patch.dict(os.environ, {}):
        with pytest.raises(SecretsManagerError) as exc_info:
            SecretsManager.load()
    assert str(exc_info.value) == "CRITICAL: Missing required environment variables: SECRET_KEY"

def test_load_optional_key_present():
    with patch.dict(os.environ, {'SECRET_KEY': 'value1', 'OPTIONAL_KEY': 'value2'}):
        result = SecretsManager.load()
    assert result == {'SECRET_KEY': 'value1', 'OPTIONAL_KEY': 'value2'}

def test_load_optional_key_absent():
    with patch.dict(os.environ, {'SECRET_KEY': 'value1'}):
        result = SecretsManager.load()
    assert result == {'SECRET_KEY': 'value1'}

def test_load_all_keys_present():
    with patch.dict(os.environ, {
        'SECRET_KEY': 'value1',
        'DATABASE_URL': 'value2',
        'OPTIONAL_KEY': 'value3'
    }):
        result = SecretsManager.load()
    assert result == {'SECRET_KEY': 'value1', 'DATABASE_URL': 'value2', 'OPTIONAL_KEY': 'value3'}

def test_load_all_keys_absent():
    with patch.dict(os.environ, {}):
        with pytest.raises(SecretsManagerError) as exc_info:
            SecretsManager.load()
    assert str(exc_info.value) == "CRITICAL: Missing required environment variables: SECRET_KEY"