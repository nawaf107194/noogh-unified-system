import os
from unittest.mock import patch
from your_module_path.secrets_manager import SecretsManager, SecretsManagerError

@pytest.fixture(autouse=True)
def setup_env_vars():
    with patch.dict(os.environ, clear=True):
        yield

def test_load_happy_path(monkeypatch):
    required_keys = ['KEY1', 'KEY2']
    optional_keys = ['OPTIONAL_KEY']
    secrets_manager = SecretsManager(required_keys, optional_keys)

    monkeypatch.setenv('KEY1', 'value1')
    monkeypatch.setenv('KEY2', 'value2')

    secrets = secrets_manager.load()

    assert secrets == {'KEY1': 'value1', 'KEY2': 'value2'}

def test_load_missing_required_key(monkeypatch):
    required_keys = ['KEY1']
    optional_keys = []
    secrets_manager = SecretsManager(required_keys, optional_keys)

    monkeypatch.setenv('KEY2', 'value2')

    with pytest.raises(SecretsManagerError) as exc_info:
        secrets_manager.load()

    assert str(exc_info.value) == "CRITICAL: Missing required environment variables: KEY1"

def test_load_with_optional_key(monkeypatch):
    required_keys = ['KEY1']
    optional_keys = ['OPTIONAL_KEY']
    secrets_manager = SecretsManager(required_keys, optional_keys)

    monkeypatch.setenv('KEY1', 'value1')
    monkeypatch.setenv('OPTIONAL_KEY', 'optional_value')

    secrets = secrets_manager.load()

    assert secrets == {'KEY1': 'value1', 'OPTIONAL_KEY': 'optional_value'}

def test_load_empty_required_keys():
    required_keys = []
    optional_keys = ['OPTIONAL_KEY']
    secrets_manager = SecretsManager(required_keys, optional_keys)

    with pytest.raises(ValueError) as exc_info:
        secrets_manager.load()

    assert str(exc_info.value) == "CRITICAL: No required keys provided"

def test_load_empty_optional_keys():
    required_keys = ['KEY1']
    optional_keys = []
    secrets_manager = SecretsManager(required_keys, optional_keys)

    monkeypatch.setenv('KEY1', 'value1')

    secrets = secrets_manager.load()

    assert secrets == {'KEY1': 'value1'}

def test_load_all_empty(monkeypatch):
    required_keys = ['KEY1']
    optional_keys = ['OPTIONAL_KEY']
    secrets_manager = SecretsManager(required_keys, optional_keys)

    with pytest.raises(SecretsManagerError) as exc_info:
        secrets_manager.load()

    assert str(exc_info.value) == "CRITICAL: Missing required environment variables: KEY1"