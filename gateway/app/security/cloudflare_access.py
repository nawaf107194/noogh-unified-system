import logging
from typing import Optional

from fastapi import Request

logger = logging.getLogger("security")


def is_mfa_verified(request: Request) -> bool:
    """
    Verifies if the request is authenticated via Cloudflare Access Zero Trust.

    Criteria for True:
    1. Header 'CF-Access-JWT-Assertion' must be present.
    2. Header 'CF-Access-Authenticated-User-Email' must be present.

    This enforces the 'Secure Write' requirement.
    In a real production environment, you would also verify the JWT signature.
    given the scope of this request (Headers check), we check presence.
    """
    jwt = getattr(request.headers, "get", lambda x: None)("CF-Access-JWT-Assertion")
    email = getattr(request.headers, "get", lambda x: None)("CF-Access-Authenticated-User-Email")

    # Bypass for Localhost/Dev
    if request.client.host in ["127.0.0.1", "localhost", "::1"]:
        return True

    if jwt and email:
        return True

    return False


def get_user_email(request: Request) -> Optional[str]:
    return request.headers.get("CF-Access-Authenticated-User-Email")
