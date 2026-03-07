import os
import logging
from typing import Optional

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)

def _get_internal_token() -> Optional[str]:
    """
    Get token at request time, not import time.
    This allows tests to run without setting env vars.
    """
    return os.getenv("NOOGH_INTERNAL_TOKEN")



def verify_internal_token(x_internal_token: str = Header(default="", alias="X-Internal-Token")):
    """
    Validate internal service token for service-to-service authentication.
    
    Checks token at request time (not import time) to allow test collection.
    """
    if not isinstance(x_internal_token, str):
        logger.error(f"🛑 [verify_internal_token] Invalid type for X-Internal-Token: {type(x_internal_token)}, expected str")
        raise HTTPException(
            status_code=400,
            detail="Invalid type for internal token, expected string"
        )

    expected = _get_internal_token()

    if not expected:
        logger.error("🛑 [verify_internal_token] NOOGH_INTERNAL_TOKEN not set in environment!")
        raise HTTPException(
            status_code=500,
            detail="Server misconfigured: NOOGH_INTERNAL_TOKEN not set"
        )

    if not x_internal_token:
        logger.warning("⚠️ [verify_internal_token] No token provided in request headers")
        raise HTTPException(
            status_code=401,
            detail="No internal token provided in request headers"
        )

    if x_internal_token != expected:
        logger.warning(f"⚠️ [verify_internal_token] Token mismatch! Received: '{x_internal_token}', Expected length: {len(expected)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid internal token"
        )

    logger.info(f"✅ [verify_internal_token] Valid token received: {x_internal_token}")
    return True

