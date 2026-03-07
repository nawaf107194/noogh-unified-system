import logging
from typing import Any, Dict

import psutil

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """
    Monitors system resources (CPU, Memory, Disk).
    """

    def __init__(self):
        logger.info("ResourceMonitor initialized.")

    def check_resources(self) -> Dict[str, Any]:
        """
        Returns snapshot of system health.
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            stats = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "status": "nominal",
            }

            if stats["cpu_percent"] > 90 or stats["memory_percent"] > 90:
                stats["status"] = "strained"
                logger.warning(f"System resources strained: {stats}")

            return stats
        except Exception as e:
            logger.error(f"Failed to check resources: {e}")
            return {"status": "error", "message": str(e)}
