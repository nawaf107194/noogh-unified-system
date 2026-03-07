import logging
import threading
import time
from collections import defaultdict
from typing import Dict, List

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class LocalhostOnlyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host
        # Allow localhost ipv4 and ipv6
        if client_host not in ("127.0.0.1", "::1", "localhost"):
            logging.warning(f"Blocked external access to internal endpoint from {client_host}")
            return Response(content="Forbidden: Internal Access Only", status_code=403)
        return await call_next(request)


class InternalRateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, max_requests_per_minute: int = 200):
        super().__init__(app)
        self.max_requests = max_requests_per_minute
        self.history: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()

        with self.lock:
            # Cleanup old
            self.history[client_ip] = [t for t in self.history[client_ip] if now - t < 60]

            if len(self.history[client_ip]) >= self.max_requests:
                return Response(content="Too Many Internal Requests", status_code=429)

            self.history[client_ip].append(now)

        return await call_next(request)


class RequestSizeLimiter(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int = 10 * 1024 * 1024):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            if int(content_length) > self.max_bytes:
                return Response(content="Payload Too Large", status_code=413)
        return await call_next(request)
