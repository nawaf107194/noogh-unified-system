import pytest
from unittest.mock import patch
import os

# Assuming _env is part of a module named evolution_config
from unified_core.evolution.evolution_config import _env

@pytest.fixture(autouse=True)
def reset_env():
    # Clear any existing environment variables before each test
    os.environ.pop('NOOGH_EVO_TEST_KEY', None)

def test_happy_path_string():
    with patch.dict(os.environ, {'NOOGH_EVO_TEST_KEY': 'value'}):
        assert _env('TEST_KEY', 'default') == 'value'

def test_happy_path_int_cast():
    with patch.dict(os.environ, {'NOOGH_EVO_TEST_KEY': '123'}):
        assert _env('TEST_KEY', 0, int) == 123

def test_default_value_used():
    assert _env('NON_EXISTENT_KEY', 'default') == 'default'

def test_empty_environment_value():
    with patch.dict(os.environ, {'NOOGH_EVO_TEST_KEY': ''}):
        assert _env('TEST_KEY', 'default') == ''

def test_none_environment_value():
    with patch.dict(os.environ, {'NOOGH_EVO_TEST_KEY': 'None'}):
        assert _env('TEST_KEY', 'default') == 'None'

def test_invalid_cast_type():
    with patch.dict(os.environ, {'NOOGH_EVO_TEST_KEY': 'abc'}):
        with pytest.raises(ValueError):
            _env('TEST_KEY', 0, int)

def test_non_convertible_cast_type():
    with patch.dict(os.environ, {'NOOGH_EVO_TEST_KEY': '123abc'}):
        with pytest.raises(ValueError):
            _env('TEST_KEY', 0, int)

def test_boundary_values():
    with patch.dict(os.environ, {'NOOGH_EVO_TEST_KEY': '2147483647'}):  # INT_MAX
        assert _env('TEST_KEY', 0, int) == 2147483647
    with patch.dict(os.environ, {'NOOGH_EVO_TEST_KEY': '-2147483648'}):  # INT_MIN
        assert _env('TEST_KEY', 0, int) == -2147483648

def test_async_behavior():
    # Since the function does not involve any async operations,
    # we can skip testing async behavior.
    pass