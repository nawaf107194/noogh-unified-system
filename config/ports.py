"""
NOOGH Port Configuration
Centralized registry for service ports to avoid collisions.
"""
import os

# Base Ports
NEURAL_PORT = int(os.getenv("NEURAL_PORT", "8002"))
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "8001"))
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Specialized Service Ports
DASHBOARD_PORT = 8080
SANDBOX_API_PORT = 8003
WEBSOCKET_PORT = 8002 # Same as Neural by default

# Centralized Port Registry
class PORTS:
    NEURAL_ENGINE = NEURAL_PORT
    GATEWAY = GATEWAY_PORT
    REDIS = REDIS_PORT
    DASHBOARD = DASHBOARD_PORT
    SANDBOX = SANDBOX_API_PORT
    MCP_EXECUTION = 8004

def get_service_url(name: str) -> str:
    """Generate local URL for a service."""
    if name == "neural":
        return f"http://127.0.0.1:{NEURAL_PORT}"
    if name == "gateway":
        return f"http://127.0.0.1:{GATEWAY_PORT}"
    return "http://localhost"
