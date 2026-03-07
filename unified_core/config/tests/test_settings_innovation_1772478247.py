import os
import sys
from unittest.mock import patch
import pytest

from unified_core.config.settings import get_env_or_fail

@pytest.fixture(autouse=True)
def reset_environment():
    # Reset environment variables before each test
    os.environ.clear()

def test_get_env_or_fail_happy_path():
    """Test happy path with normal inputs."""
    os.environ['TEST_KEY'] = 'test_value'
    assert get_env_or_fail('TEST_KEY') == 'test_value'

def test_get_env_or_fail_with_default():
    """Test with a default value provided."""
    assert get_env_or_fail('TEST_KEY', default='default_value') == 'default_value'

@patch('sys.stdout')
def test_get_env_or_fail_missing_key(mock_stdout):
    """Test missing key with no default provided."""
    with pytest.raises(SystemExit) as exc_info:
        get_env_or_fail('TEST_KEY')
    assert exc_info.value.code == 1
    mock_stdout.write.assert_called_once_with("🛑 FATAL: Missing required environment variable: TEST_KEY\n")

@patch('sys.stdout')
def test_get_env_or_fail_missing_key_with_default(mock_stdout):
    """Test missing key with default provided."""
    assert get_env_or_fail('TEST_KEY', default='default_value') == 'default_value'

@patch('sys.stdout')
def test_get_env_or_fail_non_string_key(mock_stdout):
    """Test non-string key input."""
    with pytest.raises(TypeError) as exc_info:
        get_env_or_fail(123)
    mock_stdout.write.assert_called_once_with("🛑 FATAL: Missing required environment variable: 123\n")

@patch('sys.stdout')
def test_get_env_or_fail_non_string_default(mock_stdout):
    """Test non-string default input."""
    with pytest.raises(TypeError) as exc_info:
        get_env_or_fail('TEST_KEY', default=123)
    mock_stdout.write.assert_called_once_with("🛑 FATAL: Missing required environment variable: TEST_KEY\n")

@patch('sys.stdout')
def test_get_env_or_fail_non_bool_dev_mode(mock_stdout):
    """Test non-bool dev_mode input."""
    with pytest.raises(TypeError) as exc_info:
        get_env_or_fail('TEST_KEY', dev_mode='not_a_bool')
    mock_stdout.write.assert_called_once_with("🛑 FATAL: Missing required environment variable: TEST_KEY\n")