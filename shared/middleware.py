from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit the maximum size of the request body"""

    def __init__(self, app, max_bytes: int = 1024 * 1024):  # 1MB default
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_bytes:
            return JSONResponse(status_code=413, content={"detail": "Request Entity Too Large"})

        return await call_next(request)
