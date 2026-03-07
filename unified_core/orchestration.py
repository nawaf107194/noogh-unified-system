import asyncio
import signal
import logging
import functools
from typing import Callable, List

logger = logging.getLogger("Orchestration")

def setup_signal_handlers(cleanup_callback: Callable, loop: asyncio.AbstractEventLoop = None):
    """
    Setup signal handlers for SIGINT and SIGTERM.
    
    Args:
        cleanup_callback: Async function to call for cleanup.
        loop: Event loop to add handlers to.
    """
    if loop is None:
        loop = asyncio.get_event_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(
                sig, 
                lambda: asyncio.create_task(handle_shutdown(sig, cleanup_callback))
            )
        except NotImplementedError:
            # Fallback for Windows or environments where add_signal_handler is missing
            pass

async def handle_shutdown(sig, cleanup_callback):
    """Signal handler that triggers cleanup."""
    logger.info(f"Received exit signal {sig.name}...")
    await cleanup_callback()

class LifecycleManager:
    """Manages system-wide lifecycle events."""
    
    def __init__(self):
        self._on_startup: List[Callable] = []
        self._on_shutdown: List[Callable] = []

    def on_startup(self, func: Callable):
        self._on_startup.append(func)
        return func

    def on_shutdown(self, func: Callable):
        self._on_shutdown.append(func)
        return func

    async def startup(self):
        logger.info("Starting up LifecycleManager...")
        for func in self._on_startup:
            if asyncio.iscoroutinefunction(func):
                await func()
            else:
                func()

    async def shutdown(self):
        logger.info("Shutting down LifecycleManager...")
        for func in reversed(self._on_shutdown):
            try:
                if asyncio.iscoroutinefunction(func):
                    await func()
                else:
                    func()
            except Exception as e:
                logger.error(f"Error during shutdown callback: {e}")

# Global instance
lifecycle = LifecycleManager()
