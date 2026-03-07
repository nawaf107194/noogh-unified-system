"""
Rate limiting middleware for API protection.
"""

import logging
import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter.
    """

    def __init__(self, requests_per_minute: int = 60, burst_size: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.rate = requests_per_minute / 60.0  # tokens per second

        # Storage: client_id -> (tokens, last_update)
        self.buckets: Dict[str, Tuple[float, float]] = defaultdict(lambda: (burst_size, time.time()))

        logger.info(f"RateLimiter initialized: {requests_per_minute} req/min, burst: {burst_size}")

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Use IP address as client ID
        client_ip = request.client.host if request.client else "unknown"

        # Could also use API key if available
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key}"

        return f"ip:{client_ip}"

    def _refill_bucket(self, client_id: str) -> float:
        """Refill tokens based on elapsed time."""
        tokens, last_update = self.buckets[client_id]

        now = time.time()
        elapsed = now - last_update

        # Add tokens based on rate
        tokens = min(self.burst_size, tokens + elapsed * self.rate)

        self.buckets[client_id] = (tokens, now)
        return tokens

    async def check_rate_limit(self, request: Request) -> bool:
        """
        Check if request should be allowed.

        Returns:
            True if allowed, raises HTTPException if rate limited
        """
        client_id = self._get_client_id(request)

        # Refill bucket
        tokens = self._refill_bucket(client_id)

        # Check if we have tokens
        if tokens >= 1.0:
            # Consume one token
            self.buckets[client_id] = (tokens - 1.0, time.time())
            return True
        else:
            # Rate limited
            logger.warning(f"Rate limit exceeded for {client_id}")
            raise HTTPException(
                status_code=429, detail={"error": "Rate limit exceeded", "retry_after": int((1.0 - tokens) / self.rate)}
            )

    def get_stats(self, client_id: str = None) -> Dict:
        """Get rate limiter statistics."""
        if client_id:
            tokens, last_update = self.buckets.get(client_id, (self.burst_size, time.time()))
            return {"client_id": client_id, "tokens_available": tokens, "last_update": last_update}
        else:
            return {
                "total_clients": len(self.buckets),
                "requests_per_minute": self.requests_per_minute,
                "burst_size": self.burst_size,
            }


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=60, burst_size=10)


async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware to apply rate limiting to all requests.
    """
    # Skip rate limiting for health check
    if request.url.path == "/health":
        return await call_next(request)

    try:
        await rate_limiter.check_rate_limit(request)
        response = await call_next(request)
        return response
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content=e.detail)
