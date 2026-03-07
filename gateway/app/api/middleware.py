import threading
import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.
    Limits by IP and Bearer Token.
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.history = defaultdict(list)
        self.lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        # Identify requester
        auth = request.headers.get("Authorization", "")
        ip = request.client.host
        identifier = f"{ip}:{auth}"

        now = time.time()
        with self.lock:
            # Clean up old timestamps
            self.history[identifier] = [t for t in self.history[identifier] if now - t < 60]

            if len(self.history[identifier]) >= self.requests_per_minute:
                return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})

            self.history[identifier].append(now)

        return await call_next(request)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Limits the size of the request body.
    """

    def __init__(self, app: ASGIApp, max_bytes: int = 10_000_000):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_bytes:
                    return JSONResponse(
                        status_code=413, content={"detail": f"Request limit exceeded ({self.max_bytes} bytes)"}
                    )
            except ValueError:
                pass
        return await call_next(request)
