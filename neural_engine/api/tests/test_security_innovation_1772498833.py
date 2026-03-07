import pytest
from unittest.mock import patch, mock_open
from neural_engine.api.security import _get_internal_token

def test_get_internal_token_happy_path():
    with patch.dict('os.environ', {'NOOGH_INTERNAL_TOKEN': 'test_token'}):
        assert _get_internal_token() == 'test_token'

def test_get_internal_token_empty_env_var():
    with patch.dict('os.environ', {}, clear=True):
        assert _get_internal_token() is None

def test_get_internal_token_none_env_var():
    with patch.dict('os.environ', {'NOOGH_INTERNAL_TOKEN': ''}):
        assert _get_internal_token() is None

def test_get_internal_token_no_env_var():
    with patch.dict('os.environ', {}, clear=True):
        assert _get_internal_token() is None