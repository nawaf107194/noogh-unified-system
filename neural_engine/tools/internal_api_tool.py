"""
Internal API Caller - Tool for calling Neural Engine APIs from ReAct.
Enables NOOGH to access memory, autonomic, monitoring, and specialized services.
"""

import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Internal Neural Engine base URL
NEURAL_ENGINE_BASE = "http://127.0.0.1:8002"
INTERNAL_TOKEN = "dev-token-noogh-2026"


class InternalAPICaller:
    """
    Tool for calling internal Neural Engine APIs.
    Provides access to memory, autonomic, monitoring, and specialized services.
    """
    
    def __init__(self):
        self.base_url = NEURAL_ENGINE_BASE
        self.headers = {
            "Content-Type": "application/json",
            "X-Internal-Token": INTERNAL_TOKEN
        }
        logger.info("✅ InternalAPICaller initialized")
    
    async def call_api(
        self, 
        endpoint: str, 
        method: str = "GET", 
        data: Optional[Dict[str, Any]] = None,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """
        Call an internal API endpoint.
        
        Args:
            endpoint: API path (e.g., "/api/v1/memory/recall")
            method: HTTP method (GET, POST)
            data: Request body for POST
            timeout: Request timeout
            
        Returns:
            API response as dict
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data or {})
                else:
                    return {"error": f"Unsupported method: {method}"}
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            return {"error": "API timeout", "endpoint": endpoint}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}", "endpoint": endpoint}
        except Exception as e:
            logger.error(f"❌ API call failed: {e}")
            return {"error": str(e), "endpoint": endpoint}


# Pre-defined API shortcuts for common operations
API_SHORTCUTS = {
    # Memory
    "memory_recall": {"endpoint": "/api/v1/memory/recall", "method": "POST"},
    "memory_stats": {"endpoint": "/api/v1/memory/stats", "method": "GET"},
    
    # Self-Awareness
    "self_awareness": {"endpoint": "/api/v1/self-awareness/summary", "method": "GET"},
    "self_metrics": {"endpoint": "/api/v1/self-awareness/metrics", "method": "GET"},
    
    # Autonomic
    "autonomic_status": {"endpoint": "/api/v1/autonomic/status", "method": "GET"},
    "autonomic_events": {"endpoint": "/api/v1/autonomic/events", "method": "GET"},
    "autonomic_health": {"endpoint": "/api/v1/autonomic/health", "method": "GET"},
    
    # System
    "system_status": {"endpoint": "/api/v1/system/status", "method": "GET"},
    "system_introspect": {"endpoint": "/api/v1/system/introspect", "method": "GET"},
    
    # Monitoring
    "monitoring_dashboard": {"endpoint": "/api/v1/monitoring/dashboard", "method": "GET"},
    "monitoring_cache": {"endpoint": "/api/v1/monitoring/cache", "method": "GET"},
    
    # Specialized
    "gpu_status": {"endpoint": "/api/v1/specialized/gpu/status", "method": "GET"},
    "creative_generate": {"endpoint": "/api/v1/specialized/creative/generate", "method": "POST"},
    
    # Cognitive
    "cognitive_traces": {"endpoint": "/api/v1/cognitive/traces", "method": "GET"},
    "cognitive_dashboard": {"endpoint": "/api/v1/cognitive/dashboard", "method": "GET"},
}


async def call_internal_api(shortcut: str = "", endpoint: str = "", method: str = "GET", data: Dict[str, Any] = None, **kwargs) -> str:
    """
    Execute an internal API call.
    
    Args:
        shortcut: Pre-defined shortcut name (e.g., "memory_recall", "self_awareness")
        endpoint: Direct endpoint path (if not using shortcut)
        method: HTTP method
        data: Request body
        
    Returns:
        Formatted result string
    """
    caller = InternalAPICaller()
    
    # Use shortcut if provided
    if shortcut and shortcut in API_SHORTCUTS:
        config = API_SHORTCUTS[shortcut]
        endpoint = config["endpoint"]
        method = config["method"]
    
    if not endpoint:
        available = ", ".join(API_SHORTCUTS.keys())
        return f"يجب تحديد endpoint أو shortcut. المتاح: {available}"
    
    result = await caller.call_api(endpoint, method, data)
    
    if "error" in result:
        return f"خطأ في API: {result['error']}"
    
    # Format result nicely
    import json
    formatted = json.dumps(result, ensure_ascii=False, indent=2)
    
    # Truncate if too long
    if len(formatted) > 2000:
        formatted = formatted[:2000] + "...\n[مقتطع]"
    
    return formatted


# Singleton instance
_caller_instance: Optional[InternalAPICaller] = None


def get_api_caller() -> InternalAPICaller:
    """Get singleton API caller."""
    global _caller_instance
    if _caller_instance is None:
        _caller_instance = InternalAPICaller()
    return _caller_instance
