"""
NOOGH Health Check Endpoints

Production health and readiness endpoints.

/health  - Service is alive
/ready   - Service is ready to handle requests
/metrics - Prometheus metrics
"""

from typing import Dict, Any, Callable, Optional
from unified_core.observability import get_logger

logger = get_logger("health_check")


class HealthChecker:
    """
    Health and readiness check manager.
    
    Supports:
    - Liveness checks (/health)
    - Readiness checks (/ready)
    - Component-level checks
    """
    
    def __init__(self, service_name: str):
        """
        Initialize health checker.
        
        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
        self._readiness_checks: Dict[str, Callable[[], bool]] = {}
        self._component_status: Dict[str, str] = {}
    
    # ==================================================================
    # Register Checks
    # ==================================================================
    
    def register_readiness_check(self, component: str, check_fn: Callable[[], bool]):
        """
        Register a readiness check for a component.
        
        Args:
            component: Component name (redis, agents, registry, etc.)
            check_fn: Function that returns True if component is ready
        """
        self._readiness_checks[component] = check_fn
        logger.info(f"Registered readiness check: {component}")
    
    # ==================================================================
    # Health Check
    # ==================================================================
    
    def health(self) -> Dict[str, Any]:
        """
        Liveness check - is the service alive?
        
        Returns:
            {
                "status": "healthy",
                "service": "gateway",
                "timestamp": "2026-01-21T..."
            }
        """
        from datetime import datetime
        
        return {
            "status": "healthy",
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    # ==================================================================
    # Readiness Check
    # ==================================================================
    
    def ready(self) -> Dict[str, Any]:
        """
        Readiness check - is the service ready to handle traffic?
        
        Checks all registered components.
        
        Returns:
            {
                "status": "ready" | "not_ready",
                "service": "gateway",
                "components": {
                    "redis": "operational",
                    "agents": "operational",
                    ...
                },
                "timestamp": "..."
            }
        """
        from datetime import datetime
        
        components = {}
        all_ready = True
        
        # Run all readiness checks
        for component, check_fn in self._readiness_checks.items():
            try:
                is_ready = check_fn()
                status = "operational" if is_ready else "failed"
                components[component] = status
                
                if not is_ready:
                    all_ready = False
                    logger.warning(f"Component not ready: {component}")
                    
            except Exception as e:
                components[component] = f"error: {str(e)}"
                all_ready = False
                logger.error(f"Readiness check failed for {component}: {e}")
        
        return {
            "status": "ready" if all_ready else "not_ready",
            "service": self.service_name,
            "components": components,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


# ==================================================================
# Example Readiness Checks
# ==================================================================

def check_redis_ready() -> bool:
    """Check if Redis is available"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_timeout=1)
        r.ping()
        return True
    except Exception:
        return False


def check_registry_loaded() -> bool:
    """Check if UnifiedToolRegistry is loaded"""
    try:
        from unified_core.tool_registry import get_unified_registry
        registry = get_unified_registry()
        tools = registry.list_tools()
        return len(tools) > 0
    except Exception:
        return False


def check_agents_subscribed() -> bool:
    """Check if agents are subscribed to MessageBus"""
    try:
        from unified_core.orchestration import get_message_bus
        bus = get_message_bus()
        # Check if any agents are subscribed
        return len(bus._subscribers) > 0
    except Exception:
        return False


# Example usage
if __name__ == "__main__":
    checker = HealthChecker("test-service")
    
    # Register checks
    checker.register_readiness_check("redis", check_redis_ready)
    checker.register_readiness_check("registry", check_registry_loaded)
    
    # Check health
    print("Health:", checker.health())
    
    # Check readiness
    print("Ready:", checker.ready())
