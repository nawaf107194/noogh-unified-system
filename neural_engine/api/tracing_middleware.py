
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

try:
    from observability_suite.logger import set_log_context
except ImportError:
    def set_log_context(**kwargs):
        pass

class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/health", "/"]:
             return await call_next(request)

        # Extract trace ID from header or generate new one
        trace_id = request.headers.get("X-Trace-Id") or request.headers.get("X-Request-Id") or str(uuid.uuid4())
        
        # Set in logging context
        set_log_context(trace_id=trace_id)
        
        # Pass to next handler
        response = await call_next(request)
        
        # Optionally inject back into response headers
        response.headers["X-Trace-Id"] = trace_id
        
        return response
