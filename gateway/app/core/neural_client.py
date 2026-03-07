"""
Neural Client - Secure HTTP client for noug-neural-os services.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

try:
    import httpx
except ImportError:
    httpx = None

from gateway.app.core.logging import get_logger

logger = get_logger("neural_client")


@dataclass
class NeuralResponse:
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class NeuralClient:
    def __init__(self, secrets: Dict[str, str], timeout: float = 300.0):
        self.base_url = secrets.get("NEURAL_SERVICE_URL", "http://127.0.0.1:8002")
        self.token = secrets.get("NOOGH_INTERNAL_TOKEN", "")
        self.timeout = timeout
        if httpx is None:
            logger.warning("httpx not installed - neural integration disabled")

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-Internal-Token"] = self.token
            
        # Inject Trace ID for distributed tracing
        try:
            from gateway.app.core.logging import get_log_context
            ctx = get_log_context()
            trace_id = ctx.get("trace_id") or ctx.get("request_id")
            if trace_id:
                headers["X-Trace-Id"] = str(trace_id)
        except ImportError:
            pass
            
        return headers

    async def _request(self, method: str, endpoint: str, data: Optional[dict] = None) -> NeuralResponse:
        if httpx is None:
            return NeuralResponse(success=False, error="httpx not installed")
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                else:
                    response = await client.post(url, json=data or {}, headers=headers)
                if response.status_code == 200:
                    return NeuralResponse(success=True, data=response.json())
                return NeuralResponse(success=False, error=f"HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            return NeuralResponse(success=False, error=str(e))

    async def health_check(self) -> NeuralResponse:
        return await self._request("GET", "/health")

    async def process_vision(self, image_path: str) -> NeuralResponse:
        return await self._request("POST", "/api/v1/vision/process", {"image_path": image_path})

    async def store_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> NeuralResponse:
        return await self._request("POST", "/api/v1/memory/store", {"content": content, "metadata": metadata or {}})

    async def recall_memory(self, query: str, n_results: int = 5) -> NeuralResponse:
        return await self._request("POST", "/api/v1/memory/recall", {"query": query, "n_results": n_results})

    async def trigger_dream(self, duration_minutes: int = 5) -> NeuralResponse:
        return await self._request("POST", "/api/v1/system/dream", {"duration_minutes": duration_minutes})

    async def process_cognition(
        self, text: str, context: Optional[Dict[str, Any]] = None, store_memory: bool = True
    ) -> NeuralResponse:
        return await self._request(
            "POST", "/api/v1/process", {"text": text, "context": context or {}, "store_memory": store_memory}
        )

    async def get_dashboard_data(self) -> NeuralResponse:
        return await self._request("GET", "/api/v1/monitoring/dashboard")

    async def execute_command(self, command: str) -> NeuralResponse:
        return await self._request("POST", "/api/v1/execute", {"command": command})


def get_neural_client(secrets: Dict[str, str]) -> NeuralClient:
    """Factory for NeuralClient."""
    return NeuralClient(secrets=secrets)
