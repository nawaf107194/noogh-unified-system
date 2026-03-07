import pytest
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from gateway.app.core.jwt_validator import require_role, verify_gateway_token

# Mocked dependencies
async def mock_verify_gateway_token():
    return {
        "username": "test_user",
        "role": "admin"
    }

@pytest.mark.parametrize("allowed_roles", [
    ("admin"),
    ("operator"),
    ("admin", "operator")
])
async def test_require_role_happy_path(allowed_roles):
    original_verify = verify_gateway_token
    verify_gateway_token = mock_verify_gateway_token

    try:
        check_role = require_role(*allowed_roles)
        result = await check_role()

        assert isinstance(result, dict)
        assert result["username"] == "test_user"
        assert result["role"] in allowed_roles
    finally:
        verify_gateway_token = original_verify

@pytest.mark.asyncio
async def test_require_role_empty_roles():
    with pytest.raises(HTTPException) as exc_info:
        check_role = require_role(*[])
        await check_role()

    assert exc_info.value.status_code == 403
    assert "Required role" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_require_role_none_roles():
    with pytest.raises(HTTPException) as exc_info:
        check_role = require_role(None)
        await check_role()

    assert exc_info.value.status_code == 403
    assert "Required role" in str(exc_info.value.detail)

@pytest.mark.parametrize("allowed_roles, user_role", [
    (("admin", "operator"), "user"),
    (("admin",), "admin"),
    (("operator",), "operator")
])
async def test_require_role_edge_cases(allowed_roles, user_role):
    async def mock_verify_gateway_token():
        return {
            "username": "test_user",
            "role": user_role
        }

    original_verify = verify_gateway_token
    verify_gateway_token = mock_verify_gateway_token

    try:
        check_role = require_role(*allowed_roles)
        with pytest.raises(HTTPException) as exc_info:
            await check_role()

        assert exc_info.value.status_code == 403
        assert "Required role" in str(exc_info.value.detail)
    finally:
        verify_gateway_token = original_verify

@pytest.mark.asyncio
async def test_require_role_async_behavior():
    async def mock_verify_gateway_token():
        return {
            "username": "test_user",
            "role": "admin"
        }

    original_verify = verify_gateway_token
    verify_gateway_token = mock_verify_gateway_token

    try:
        check_role = require_role("admin")
        result = await check_role()
        assert isinstance(result, dict)
        assert result["username"] == "test_user"
        assert result["role"] == "admin"
    finally:
        verify_gateway_token = original_verify