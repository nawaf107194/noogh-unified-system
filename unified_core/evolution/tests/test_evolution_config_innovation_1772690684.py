import pytest
import os
from src.unified_core.evolution.evolution_config import _env

@pytest.fixture
def mock_env(monkeypatch):
    """Fixture to mock environment variables for testing."""
    def _set_env(key: str, value: str):
        monkeypatch.setenv(f"NOOGH_EVO_{key}", value)
    return _set_env

def test_env_happy_path(mock_env):
    """Test normal operation with existing env variable."""
    mock_env("TEST_KEY", "test_value")
    assert _env("TEST_KEY", default="default") == "test_value"

def test_env_default_value():
    """Test default value is returned when env var doesn't exist."""
    assert _env("NON_EXISTENT_KEY", default="default") == "default"

def test_env_int_cast(mock_env):
    """Test integer casting."""
    mock_env("INT_KEY", "123")
    assert _env("INT_KEY", default=0, cast=int) == 123

def test_env_float_cast(mock_env):
    """Test float casting."""
    mock_env("FLOAT_KEY", "12.34")
    assert _env("FLOAT_KEY", default=0.0, cast=float) == 12.34

def test_env_bool_cast(mock_env):
    """Test boolean casting."""
    mock_env("BOOL_KEY", "True")
    assert _env("BOOL_KEY", default=False, cast=bool) is True

def test_env_no_cast(mock_env):
    """Test no casting is applied by default."""
    mock_env("NO_CAST_KEY", "test_string")
    assert _env("NO_CAST_KEY", default="default") == "test_string"

def test_env_empty_string(mock_env):
    """Test empty string handling."""
    mock_env("EMPTY_KEY", "")
    assert _env("EMPTY_KEY", default="default") == ""

def test_env_none_value():
    """Test None value handling."""
    assert _env("NONE_KEY", default=None) is None

def test_env_cast_failure(mock_env):
    """Test invalid casting scenario."""
    mock_env("CAST_KEY", "invalid_int")
    assert _env("CAST_KEY", default=0, cast=int) == 0  # Should fall back to default

def test_env_case_sensitive(mock_env):
    """Test case sensitivity of environment variables."""
    mock_env("CASE_KEY", "Value")
    assert _env("CASE_KEY", default="default") == "Value"