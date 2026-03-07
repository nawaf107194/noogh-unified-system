"""
JWT Token Validator for Gateway

Validates JWT tokens issued by Dashboard API to enable unified authentication
across legacy Gateway and new Dashboard API.

Usage:
    from gateway.app.core.jwt_validator import verify_gateway_token, require_role
    
    @router.get("/protected")
    async def protected_endpoint(user: dict = Depends(verify_gateway_token)):
        # user = {"username": "admin", "role": "admin"}
        ...
"""

import os
import jwt
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from unified_core.observability import get_logger

logger = get_logger("gateway.auth")

# Shared JWT secret (must match Dashboard API)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION_PLEASE")
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


async def verify_gateway_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Verify JWT token from Dashboard API
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        dict: User context {"username": str, "role": str, "email": str}
        
    Raises:
        HTTPException: 401 if token invalid/expired, 403 if no token provided
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please login.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        username = payload.get("sub")
        role = payload.get("role")
        
        if not username or not role:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload"
            )
        
        user_context = {
            "username": username,
            "role": role,
        }
        
        logger.info(f"Token validated for user: {username} (role: {role})")
        
        return user_context
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=401,
            detail="Token has expired. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal authentication error"
        )


def require_role(*allowed_roles: str):
    """
    Dependency factory for role-based access control
    
    Args:
        *allowed_roles: Roles that are allowed (e.g., "admin", "operator")
        
    Usage:
        @router.post("/control", dependencies=[Depends(require_role("operator", "admin"))])
        async def control_endpoint():
            ...
    
    Returns:
        Dependency function that checks role
    """
    async def check_role(user: dict = Depends(verify_gateway_token)) -> dict:
        user_role = user.get("role")
        
        if user_role not in allowed_roles:
            logger.warning(
                f"Access denied for user {user['username']} "
                f"(role: {user_role}, required: {allowed_roles})"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {', '.join(allowed_roles)}"
            )
        
        return user
    
    return check_role
