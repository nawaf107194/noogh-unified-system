import pytest
from fastapi import Request, HTTPException, Header
from unittest.mock import patch

from src.unified_core.auth import require_bearer, AuthContext

# Mocked secrets data for testing
MOCK_SECRETS = {
    "valid_token": ["read", "write"],
    "another_valid_token": ["read"]
}

@pytest.fixture(scope="module")
def request_mock():
    class MockRequest:
        def __init__(self, state=None):
            self.state = state or {}

    return MockRequest({"secrets": MOCK_SECRETS})

def test_happy_path(request_mock):
    authorization_header = "Bearer valid_token"
    auth_context = require_bearer(Request(state=request_mock.state), authorization=authorization_header)
    assert isinstance(auth_context, AuthContext)
    assert auth_context.token == "valid_token"
    assert auth_context.scopes == ["read", "write"]

def test_empty_authorization_header(request_mock):
    with pytest.raises(HTTPException) as exc_info:
        require_bearer(Request(state=request_mock.state), authorization="")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing Bearer token"

def test_missing_authorization_header(request_mock):
    with pytest.raises(HTTPException) as exc_info:
        require_bearer(Request(state=request_mock.state))
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing Bearer token"

def test_invalid_token_format(request_mock):
    authorization_header = "Bearer invalid_token"
    with pytest.raises(HTTPException) as exc_info:
        require_bearer(Request(state=request_mock.state), authorization=authorization_header)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing Bearer token"

def test_unknown_token(request_mock):
    authorization_header = "Bearer unknown_token"
    with pytest.raises(HTTPException) as exc_info:
        require_bearer(Request(state=request_mock.state), authorization=authorization_header)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"

# Async behavior is not applicable here as the function does not contain async operations