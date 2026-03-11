"""Base Agent - Unified base class for all NOOGH agents."""
from abc import ABC, abstractmethod
import asyncio
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Unified base class for all NOOGH agents."""

    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self._running = False
        self._start_time: Optional[float] = None
        self._cycle_count = 0
        self._error_count = 0
        self.logger = logging.getLogger(self.name)

    # ─── Abstract Interface ───────────────────────────────────────────────────

    @abstractmethod
    async def start(self):
        """Start the agent's main loop."""
        pass

    @abstractmethod
    async def stop(self):
        """Stop the agent's main loop."""
        pass

    @abstractmethod
    async def process(self, data: Any):
        """Process incoming data."""
        pass

    # ─── Run Loop ─────────────────────────────────────────────────────────────

    async def run(self, interval: float = 1.0):
        """Main run loop - calls process() periodically."""
        self._running = True
        self._start_time = time.time()
        self.logger.info(f"[{self.name}] started")
        while self._running:
            try:
                self._cycle_count += 1
                await self.process(None)
            except Exception as e:
                self._error_count += 1
                self.logger.error(f"[{self.name}] cycle error: {e}")
            await asyncio.sleep(interval)
        self.logger.info(f"[{self.name}] stopped after {self._cycle_count} cycles")

    # ─── Utilities ────────────────────────────────────────────────────────────

    def is_running(self) -> bool:
        return self._running

    def uptime(self) -> float:
        """Return uptime in seconds."""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    def stats(self) -> dict:
        return {
            "name": self.name,
            "running": self._running,
            "uptime_s": round(self.uptime(), 1),
            "cycles": self._cycle_count,
            "errors": self._error_count,
        }

    def __repr__(self):
        return f"<{self.name} running={self._running} cycles={self._cycle_count}>"
