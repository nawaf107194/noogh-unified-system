import pytest
from unittest.mock import patch, mock_open
from fastapi import Header, HTTPException

from neural_engine.api.auth import optional_internal_token

def test_happy_path():
    with patch.dict("os.environ", {"NOOGH_INTERNAL_TOKEN": "expected_token"}):
        assert optional_internal_token(x_internal_token="expected_token") == True

def test_empty_env_var_no_header():
    with patch.dict("os.environ", {"NOOGH_INTERNAL_TOKEN": ""}):
        assert optional_internal_token() == True

def test_empty_token_header():
    with patch.dict("os.environ", {"NOOGH_INTERNAL_TOKEN": "expected_token"}):
        assert optional_internal_token(x_internal_token="") == False

def test_none_token_header():
    with patch.dict("os.environ", {"NOOGH_INTERNAL_TOKEN": "expected_token"}):
        assert optional_internal_token(x_internal_token=None) == False

def test_mismatched_tokens():
    with patch.dict("os.environ", {"NOOGH_INTERNAL_TOKEN": "expected_token"}):
        assert optional_internal_token(x_internal_token="wrong_token") == False