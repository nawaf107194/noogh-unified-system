import os
from unittest.mock import patch
from fastapi import HTTPException
from typing import Optional

from neural_engine.api.auth import optional_internal_token, Header

@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {'NOOGH_INTERNAL_TOKEN': 'test_token'}):
        yield

def test_optional_internal_token_happy_path(mock_env):
    request = Mock()
    setattr(request, "headers", {"x-internal-token": "test_token"})
    
    result = optional_internal_token(Header(default=None))(request)
    
    assert result is True

def test_optional_internal_token_empty_header(mock_env):
    request = Mock()
    setattr(request, "headers", {})
    
    result = optional_internal_token(Header(default=None))(request)
    
    assert result is False

def test_optional_internal_token_none_header(mock_env):
    request = Mock()
    setattr(request, "headers", {"x-internal-token": None})
    
    result = optional_internal_token(Header(default=None))(request)
    
    assert result is False

def test_optional_internal_token_different_token(mock_env):
    request = Mock()
    setattr(request, "headers", {"x-internal-token": "wrong_token"})
    
    result = optional_internal_token(Header(default=None))(request)
    
    assert result is False

def test_optional_internal_token_missing_env_var():
    with patch.dict(os.environ, {'NOOGH_INTERNAL_TOKEN': ''}):
        request = Mock()
        setattr(request, "headers", {"x-internal-token": "test_token"})
        
        result = optional_internal_token(Header(default=None))(request)
        
        assert result is True

def test_optional_internal_token_empty_string_token():
    with patch.dict(os.environ, {'NOOGH_INTERNAL_TOKEN': '  '}):
        request = Mock()
        setattr(request, "headers", {"x-internal-token": ""})
        
        result = optional_internal_token(Header(default=None))(request)
        
        assert result is False

def test_optional_internal_token_none_env_var():
    with patch.dict(os.environ, {'NOOGH_INTERNAL_TOKEN': None}):
        request = Mock()
        setattr(request, "headers", {"x-internal-token": "test_token"})
        
        result = optional_internal_token(Header(default=None))(request)
        
        assert result is True