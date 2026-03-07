import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import Request, HTTPException
from starlette.datastructures import Headers
from app.api.auth import AuthContext, require_bearer
from app.api.routes import require_admin

@pytest.fixture
def mock_request():
    request = MagicMock(spec=Request)
    request.headers = Headers()
    request.app.state.secrets = {}
    return request

@pytest.fixture
def mock_auth_context():
    return AuthContext(token="mocked_admin_token")

@pytest.fixture
def mock_is_mfa_verified():
    return AsyncMock(return_value=True)

@pytest.fixture
def mock_hmac_compare_digest(monkeypatch):
    def compare_digest_side_effect(a, b):
        return a == b
    monkeypatch.setattr('hmac.compare_digest', compare_digest_side_effect)

@pytest.mark.asyncio
async def test_require_admin_happy_path(mock_request, mock_auth_context, mock_is_mfa_verified, mock_hmac_compare_digest):
    mock_request.app.state.secrets["NOOGH_ADMIN_TOKEN"] = "mocked_admin_token"
    result = await require_admin(mock_request, mock_auth_context)
    assert result == mock_auth_context

@pytest.mark.asyncio
async def test_require_admin_without_mfa(mock_request, mock_auth_context, mock_is_mfa_verified, mock_hmac_compare_digest):
    mock_is_mfa_verified.return_value = False
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(mock_request, mock_auth_context)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Cloudflare Access MFA Required"

@pytest.mark.asyncio
async def test_require_admin_missing_admin_token(mock_request, mock_auth_context, mock_is_mfa_verified, mock_hmac_compare_digest):
    mock_request.app.state.secrets = {}
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(mock_request, mock_auth_context)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Server config error: admin token missing"

@pytest.mark.asyncio
async def test_require_admin_invalid_admin_token(mock_request, mock_auth_context, mock_is_mfa_verified, mock_hmac_compare_digest):
    mock_request.app.state.secrets["NOOGH_ADMIN_TOKEN"] = "wrong_token"
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(mock_request, mock_auth_context)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Admin access required"

@pytest.mark.asyncio
async def test_require_admin_none_auth_token(mock_request, mock_auth_context, mock_is_mfa_verified, mock_hmac_compare_digest):
    mock_auth_context.token = None
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(mock_request, mock_auth_context)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Admin access required"

@pytest.mark.asyncio
async def test_require_admin_empty_auth_token(mock_request, mock_auth_context, mock_is_mfa_verified, mock_hmac_compare_digest):
    mock_auth_context.token = ""
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(mock_request, mock_auth_context)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Admin access required"