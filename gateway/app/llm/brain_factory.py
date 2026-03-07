from typing import Dict, Optional, Union

from gateway.app.core.config import get_settings
from gateway.app.core.logging import get_logger
from gateway.app.llm.cloud_client import CloudClient
from gateway.app.llm.local_brain import LocalBrainService
from gateway.app.llm.remote_brain import RemoteBrainService

logger = get_logger("brain_factory")
settings = get_settings()

# Singleton instance
_brain_instance: Optional[Union[LocalBrainService, CloudClient, RemoteBrainService]] = None


def get_brain_service() -> Optional[Union[LocalBrainService, CloudClient, RemoteBrainService]]:
    """Get the active brain service singleton"""
    return _brain_instance


def create_brain(secrets: Dict[str, str]) -> Union[LocalBrainService, CloudClient, RemoteBrainService]:
    """
    Factory to create the appropriate Brain service implementation
    based on configuration (ROUTING_MODE, CLOUD_API_KEY).
    """
    global _brain_instance

    # If already created, return it? No, create_brain implies creation.
    # But usually lifespan calls create_brain once.

    try:
        mode = settings.ROUTING_MODE.lower()
        use_cloud = False
        api_key = secrets.get("CLOUD_API_KEY")
        provider = secrets.get("CLOUD_PROVIDER")

        service = None

        # Determine intent
        if mode == "cloud":
            use_cloud = True
        elif mode == "auto" and api_key:
            use_cloud = True

        # Instantiate
        if use_cloud and api_key:
            logger.info(f"BrainFactory: Initializing CloudClient ({provider})")
            service = CloudClient(secrets=secrets)
        else:
            logger.info("BrainFactory: Initializing LocalBrainService")
            service = LocalBrainService(secrets=secrets)

        _brain_instance = service
        return service

    except Exception as e:
        logger.error(f"BrainFactory Error: {e}")
        # Fail-safe
        service = LocalBrainService(secrets=secrets)
        _brain_instance = service
        return service
