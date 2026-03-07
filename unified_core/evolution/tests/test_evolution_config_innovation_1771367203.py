import pytest
from unittest.mock import patch
import os

# Assuming the function _env is defined in a module named evolution_config
from unified_core.evolution.evolution_config import _env

@pytest.fixture(autouse=True)
def reset_environment():
    # Reset environment variables before each test
    os.environ.pop("NOOGH_EVO_TEST_KEY", None)

def test_happy_path_str():
    with patch.dict('os.environ', {"NOOGH_EVO_TEST_KEY": "test_value"}):
        assert _env("TEST_KEY", default="default_value") == "test_value"

def test_happy_path_int():
    with patch.dict('os.environ', {"NOOGH_EVO_TEST_KEY": "123"}):
        assert _env("TEST_KEY", default=0, cast=int) == 123

def test_happy_path_float():
    with patch.dict('os.environ', {"NOOGH_EVO_TEST_KEY": "123.456"}):
        assert _env("TEST_KEY", default=0.0, cast=float) == 123.456

def test_happy_path_bool_true():
    with patch.dict('os.environ', {"NOOGH_EVO_TEST_KEY": "True"}):
        assert _env("TEST_KEY", default=False, cast=bool) == True

def test_happy_path_bool_false():
    with patch.dict('os.environ', {"NOOGH_EVO_TEST_KEY": "False"}):
        assert _env("TEST_KEY", default=True, cast=bool) == False

def test_edge_case_empty_env_variable():
    with patch.dict('os.environ', {"NOOGH_EVO_TEST_KEY": ""}):
        assert _env("TEST_KEY", default="default_value") == ""

def test_edge_case_none_env_variable():
    with patch.dict('os.environ', {"NOOGH_EVO_TEST_KEY": None}):
        assert _env("TEST_KEY", default="default_value") == "default_value"

def test_edge_case_default_value_used():
    with patch.dict('os.environ', {}):
        assert _env("TEST_KEY", default="default_value") == "default_value"

def test_error_case_invalid_cast_to_int():
    with patch.dict('os.environ', {"NOOGH_EVO_TEST_KEY": "not_an_int"}):
        with pytest.raises(ValueError):
            _env("TEST_KEY", default=0, cast=int)

def test_error_case_invalid_cast_to_float():
    with patch.dict('os.environ', {"NOOGH_EVO_TEST_KEY": "not_a_float"}):
        with pytest.raises(ValueError):
            _env("TEST_KEY", default=0.0, cast=float)

def test_error_case_invalid_cast_to_bool():
    with patch.dict('os.environ', {"NOOGH_EVO_TEST_KEY": "not_a_bool"}):
        with pytest.raises(ValueError):
            _env("TEST_KEY", default=True, cast=bool)

# Since the function does not have any async behavior, we skip the async behavior tests.