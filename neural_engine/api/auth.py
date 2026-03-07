"""
Internal authentication for noug-neural-os services.
Only allows connections from NOOGH gateway with valid internal token.
"""

import os
from typing import Optional

from fastapi import Header, HTTPException


def require_internal_token(x_internal_token: Optional[str] = Header(default=None)) -> None:
    """
    Authentication for internal service calls from NOOGH.

    Args:
        x_internal_token: Token passed in X-Internal-Token header

    Raises:
        HTTPException: 500 if token not configured, 403 if invalid
    """
    expected = os.getenv("NOOGH_INTERNAL_TOKEN", "").strip()

    # Fail closed: if no token configured, reject all requests
    if not expected:
        import logging
        logging.getLogger("neural_engine.auth").error(
            "SECURITY: NOOGH_INTERNAL_TOKEN not configured — rejecting request (fail-closed)"
        )
        raise HTTPException(status_code=500, detail="Internal token not configured")

    if not x_internal_token:
        raise HTTPException(status_code=403, detail="Missing internal token")

    if x_internal_token.strip() != expected:
        raise HTTPException(status_code=403, detail="Invalid internal token")


def optional_internal_token(x_internal_token: Optional[str] = Header(default=None)) -> bool:
    """
    Optional authentication - returns True if valid, False otherwise.
    Useful for endpoints that work differently based on caller.
    """
    expected = os.getenv("NOOGH_INTERNAL_TOKEN", "").strip()

    if not expected:
        return True  # Dev mode

    if not x_internal_token:
        return False

    return x_internal_token.strip() == expected
