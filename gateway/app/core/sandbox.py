import abc
import logging
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger("sandbox")


class SandboxService(abc.ABC):
    """Abstract interface for code execution sandboxes."""

    @abc.abstractmethod
    def execute_code(self, code: str, language: str = "python", timeout: int = 10) -> Dict[str, Any]:
        """
        Execute code in the sandbox.
        Returns:
            Dict with keys: success, output, error, exit_code, duration_ms
        """


class RemoteSandboxService(SandboxService):
    """
    Delegates execution to the isolated Sandbox Service via HTTP.
    """

    def __init__(self, service_url: str):
        if not service_url:
            raise ValueError("service_url is required for RemoteSandboxService")
        self.service_url = service_url.rstrip("/")
        self.client_timeout = 5  # Connect timeout

    def execute_code(self, code: str, language: str = "python", timeout: int = 10) -> Dict[str, Any]:
        start_time = time.time()
        try:
            payload = {"code": code, "language": language, "timeout": timeout}
            # Add Internal Auth if needed later. For now, network isolation.

            # Request timeout = execution_timeout + buffer
            resp = requests.post(f"{self.service_url}/execute", json=payload, timeout=timeout + 2)

            if resp.status_code != 200:
                logger.error(f"Sandbox Service returned {resp.status_code}: {resp.text}")
                return {
                    "success": False,
                    "output": "",
                    "error": f"Sandbox Service Error ({resp.status_code})",
                    "exit_code": -1,
                    "duration_ms": (time.time() - start_time) * 1000,
                }

            return resp.json()

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "output": "",
                "error": f"Sandbox Request Timed Out (> {timeout}s)",
                "exit_code": -1,
                "duration_ms": (time.time() - start_time) * 1000,
            }
        except Exception as e:
            logger.error(f"Remote Sandbox Call Failed: {e}")
            return {
                "success": False,
                "output": "",
                "error": f"Connection Error: {str(e)}",
                "exit_code": -1,
                "duration_ms": (time.time() - start_time) * 1000,
            }


def get_sandbox_service(service_url: str) -> Optional[SandboxService]:
    """Factory to get the configured sandbox service."""
    try:
        # Returns remote service client
        return RemoteSandboxService(service_url=service_url)
    except Exception as e:
        logger.error(f"Failed to initialize sandbox client: {e}")
        return None
