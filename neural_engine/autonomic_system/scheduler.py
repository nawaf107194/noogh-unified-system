import asyncio
import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class Scheduler:
    """
    Manages periodic background tasks (Heartbeat, Cleanup, etc.).
    """

    def __init__(self):
        self.tasks: List[Dict[str, Any]] = []
        logger.info("Scheduler initialized.")

    def schedule(self, name: str, interval: int, func: Callable):
        """
        Register a task to run every `interval` seconds.
        """
        self.tasks.append({"name": name, "interval": interval, "func": func, "last_run": 0})
        logger.info(f"Scheduled task '{name}' every {interval}s")

    async def run_pending(self):
        """
        Run tasks that are due. (To be called in the main loop).
        """
        import time

        now = time.time()

        for task in self.tasks:
            if now - task["last_run"] >= task["interval"]:
                logger.debug(f"Running periodic task: {task['name']}")
                try:
                    if asyncio.iscoroutinefunction(task["func"]):
                        await task["func"]()
                    else:
                        task["func"]()
                    task["last_run"] = now
                except Exception as e:
                    logger.error(f"Task '{task['name']}' failed: {e}")
