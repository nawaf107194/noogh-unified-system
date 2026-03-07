import pytest
from fastapi import HTTPException
from unittest.mock import patch

from gateway.app.core.jwt_validator import require_role, verify_gateway_token

@pytest.mark.asyncio
async def test_require_role_happy_path():
    allowed_roles = ["operator", "admin"]
    
    @patch("gateway.app.core.jwt_validator.verify_gateway_token", return_value={"username": "testuser", "role": "operator"})
    async def control_endpoint(mock_verify):
        check_role = require_role(*allowed_roles)
        result = await check_role()
        assert result == {"username": "testuser", "role": "operator"}

@pytest.mark.asyncio
async def test_require_role_empty_allowed_roles():
    allowed_roles = []
    
    with pytest.raises(HTTPException) as exc_info:
        @patch("gateway.app.core.jwt_validator.verify_gateway_token", return_value={"username": "testuser", "role": "operator"})
        async def control_endpoint(mock_verify):
            check_role = require_role(*allowed_roles)
            await check_role()

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions. Required role: "

@pytest.mark.asyncio
async def test_require_role_no_user_role():
    allowed_roles = ["operator", "admin"]
    
    with pytest.raises(HTTPException) as exc_info:
        @patch("gateway.app.core.jwt_validator.verify_gateway_token", return_value={"username": "testuser"})
        async def control_endpoint(mock_verify):
            check_role = require_role(*allowed_roles)
            await check_role()

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions. Required role: operator, admin"

@pytest.mark.asyncio
async def test_require_role_user_not_allowed():
    allowed_roles = ["operator", "admin"]
    
    with pytest.raises(HTTPException) as exc_info:
        @patch("gateway.app.core.jwt_validator.verify_gateway_token", return_value={"username": "testuser", "role": "viewer"})
        async def control_endpoint(mock_verify):
            check_role = require_role(*allowed_roles)
            await check_role()

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions. Required role: operator, admin"

@pytest.mark.asyncio
async def test_require_role_user_role_not_string():
    allowed_roles = ["operator", "admin"]
    
    with pytest.raises(HTTPException) as exc_info:
        @patch("gateway.app.core.jwt_validator.verify_gateway_token", return_value={"username": "testuser", "role": 123})
        async def control_endpoint(mock_verify):
            check_role = require_role(*allowed_roles)
            await check_role()

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions. Required role: operator, admin"