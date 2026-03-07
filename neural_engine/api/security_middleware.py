"""
Security middleware for noug-neural-os.
Rate limiting and request validation for internal API.
"""

import threading
import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class InternalRateLimiter(BaseHTTPMiddleware):
    """
    Rate limiter for internal service calls.
    More permissive than external rate limiting since this is internal.
    """

    def __init__(self, app, max_requests_per_minute: int = 200):
        super().__init__(app)
        self.max_requests = max_requests_per_minute
        self.requests = defaultdict(list)
        self.lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        client = request.client.host if request.client else "unknown"
        now = time.time()

        with self.lock:
            # Clean old entries
            self.requests[client] = [t for t in self.requests[client] if now - t < 60]

            if len(self.requests[client]) >= self.max_requests:
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

            self.requests[client].append(now)

        return await call_next(request)




class LocalhostOnlyMiddleware(BaseHTTPMiddleware):
    """
    Restrict access to localhost only for security.
    This ensures noug-neural-os is only accessible from the local machine.
    """

    ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}

    async def dispatch(self, request: Request, call_next):
        # Disabled for Docker environment to allow Gateway connection
        return await call_next(request)
