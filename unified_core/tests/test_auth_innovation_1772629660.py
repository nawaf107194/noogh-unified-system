import pytest
from fastapi import HTTPException
from unittest.mock import Mock
from auth import require_admin

def test_require_admin_happy_path():
    # Test normal case where admin access is granted
    auth = Mock()
    auth.scopes = {"*"}
    
    result = require_admin(auth)
    
    assert result == auth

def test_require_admin_empty_scopes():
    # Test edge case with empty scopes
    auth = Mock()
    auth.scopes = set()
    
    with pytest.raises(HTTPException) as exc_info:
        require_admin(auth)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Admin access required"

def test_require_admin_scopes_none():
    # Test edge case where scopes is None
    auth = Mock()
    auth.scopes = None
    
    with pytest.raises(AttributeError):
        require_admin(auth)

def test_require_admin_invalid_scopes():
    # Test error case where invalid scopes are provided
    auth = Mock()
    auth.scopes = {"read", "write"}
    
    with pytest.raises(HTTPException) as exc_info:
        require_admin(auth)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Admin access required"