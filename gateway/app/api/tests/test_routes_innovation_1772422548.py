import pytest
from fastapi import HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

# Mocks for dependencies and utility functions
class MockAuthContext:
    def __init__(self, token):
        self.token = token

def mock_require_bearer():
    return MockAuthContext("mock_token")

def mock_is_mfa_verified(request: Request):
    return True

# Patch the dependencies and utilities in the module under test
from gateway.app.api.routes import require_admin

@pytest.fixture(autouse=True)
def patch_module():
    from unittest.mock import patch

    with patch('gateway.app.api.routes.require_bearer', mock_require_bearer), \
         patch('gateway.app.api.routes.is_mfa_verified', mock_is_mfa_verified):
        yield

# Happy path test
def test_require_admin_happy_path():
    request = Request(scope={"type": "http"})
    result = require_admin(request)
    assert isinstance(result, MockAuthContext)
    assert result.token == "mock_token"

# Edge case tests
def test_require_admin_empty_token():
    request = Request(scope={"type": "http"})
    def mock_require_bearer():
        return MockAuthContext(None)
    
    with patch('gateway.app.api.routes.require_bearer', mock_require_bearer):
        with pytest.raises(HTTPException) as exc_info:
            require_admin(request)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Admin access required"

def test_require_admin_missing_token():
    request = Request(scope={"type": "http"})
    secrets = {}
    setattr(request.app.state, "secrets", secrets)
    
    with pytest.raises(HTTPException) as exc_info:
        require_admin(request)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Server config error: admin token missing"

# Error case tests (none explicitly raised in the provided code)

# Async behavior test (not applicable since there are no async calls)