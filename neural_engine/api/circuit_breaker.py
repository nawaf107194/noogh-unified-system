import asyncio
from typing import Optional, TypeVar, Callable, Any
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED (working), OPEN (broken), HALF-OPEN (testing)

    async def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        # Simplified for now: Just pass through or fail
        # Ideally would track state.
        # For this phase, we care more about Concurrency Limiting (Semaphore) + Timeouts.
        pass

class GpuGuard:
    """
    Protects GPU resources with a Semaphore and strict Timeouts.
    Functions as a bulkhead pattern.
    """
    def __init__(self, max_concurrent: int = 1, timeout_seconds: int = 30):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.timeout = timeout_seconds

    async def run(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        try:
            async with self.semaphore:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=self.timeout)
        except asyncio.TimeoutError:
            logger.error(f"GPU Operation timed out after {self.timeout}s")
            raise Exception("System Overloaded: GPU processing timed out.")
        except Exception as e:
            logger.error(f"GPU Operation failed: {e}")
            raise
