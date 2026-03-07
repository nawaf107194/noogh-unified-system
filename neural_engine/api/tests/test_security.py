import pytest
from os import environ, getenv
from neural_engine.api.security import _get_internal_token

@pytest.fixture
def mock_env():
    original_value = environ.get("NOOGH_INTERNAL_TOKEN")
    yield None  # Simulate the environment variable being unset or empty
    if original_value is not None:
        environ["NOOGH_INTERNAL_TOKEN"] = original_value

@pytest.mark.parametrize("env_value, expected", [
    (None, None),
    ("", None),
    ("valid_token", "valid_token")
])
def test_get_internal_token(mock_env, env_value):
    with environ_context({"NOOGH_INTERNAL_TOKEN": env_value}):
        assert _get_internal_token() == expected

def test_get_internal_token_no_environment_variable():
    with mock_env:
        assert _get_internal_token() is None