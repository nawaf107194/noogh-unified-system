import logging
from typing import Any, Dict
import psutil
from gateway.app.core.jobs import get_job_store

# إعداد المسجل
logger = logging.getLogger("health")

class AdvancedHealthProbe:
    def __init__(self):
        pass

    def check_liveness(self) -> Dict[str, str]:
        return {"status": "alive"}

    def check_readiness(self) -> Dict[str, Any]:
        """Check if system dependencies are ready."""
        status = {
            "redis": False, 
            "neural_engine": False, 
            "ready": False,
            "details": {}
        }

        # 1. Check Redis
        try:
            from gateway.app.security.secrets_manager import SecretsManager
            secrets = SecretsManager.load()
            store = get_job_store(secrets)
            if hasattr(store, "redis"):
                store.redis.ping()
                status["redis"] = True
                status["details"]["redis"] = "Connected"
            else:
                status["details"]["redis"] = "Not configured"
        except Exception as e:
            status["details"]["redis"] = f"Error: {str(e)}"

        # 2. Check Neural Engine
        try:
            import httpx
            import os
            neural_url = os.getenv("NEURAL_ENGINE_URL", "http://127.0.0.1:8002")
            
            with httpx.Client(timeout=3.0) as client:
                response = client.get(f"{neural_url}/health")
                if response.status_code == 200:
                    status["neural_engine"] = True
                    status["details"]["neural_engine"] = response.json()
                else:
                    status["details"]["neural_engine"] = f"Status {response.status_code}"
        except Exception as e:
            status["details"]["neural_engine"] = f"Unreachable: {str(e)}"

        # Overall readiness
        status["ready"] = status["redis"] and status["neural_engine"]
        return status

    def run_diagnostics(self) -> Dict[str, Any]:
        return {"system": "healthy"}

health_probe = AdvancedHealthProbe()
