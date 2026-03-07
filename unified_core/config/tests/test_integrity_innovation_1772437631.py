import pytest
from unified_core.config.integrity import verify_integrity, ConfigurationTamperError

# Mock settings and allowlist integrity for testing
settings = type('Settings', (object,), {
    'FILESYSTEM_ALLOWLIST': {'key': 'value'},
    'NETWORK_ALLOWLIST': {'key': 'value'},
    'PROCESS_ALLOWLIST': {'key': 'value'}
})

_ALLOWLIST_INTEGRITY = {
    "filesystem": hashlib.sha256(str(settings.FILESYSTEM_ALLOWLIST).encode()).hexdigest(),
    "network": hashlib.sha256(str(settings.NETWORK_ALLOWLIST).encode()).hexdigest(),
    "process": hashlib.sha256(str(settings.PROCESS_ALLOWLIST).encode()).hexdigest()
}

def test_verify_integrity_happy_path():
    assert verify_integrity() is None

def test_verify_integrity_empty_allowlist():
    settings.FILESYSTEM_ALLOWLIST = {}
    with pytest.raises(ConfigurationTamperError):
        verify_integrity()

def test_verify_integrity_none_allowlist():
    settings.FILESYSTEM_ALLOWLIST = None
    with pytest.raises(ConfigurationTamperError):
        verify_integrity()

def test_verify_integrity_boundary_allowlist():
    settings.FILESYSTEM_ALLOWLIST = {'key': 'boundary_value'}
    _ALLOWLIST_INTEGRITY["filesystem"] = hashlib.sha256(str(settings.FILESYSTEM_ALLOWLIST).encode()).hexdigest()
    assert verify_integrity() is None

def test_verify_integrity_invalid_input():
    # This case does not apply as the function does not accept any parameters
    pass