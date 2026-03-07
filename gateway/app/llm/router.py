
from gateway.app.core.config import get_settings
from gateway.app.core.logging import get_logger

settings = get_settings()
logger = get_logger("router")


class HybridRouter:
    def __init__(self):
        self.default_mode = settings.ROUTING_MODE

    def route(self, prompt: str, mode: str = "auto", allow_exec: bool = False) -> str:
        """
        Returns: 'local' | 'cloud'
        """
        effective_mode = mode if mode in ["local", "cloud", "auto"] else self.default_mode

        logger.info(f"Routing Request: Mode={effective_mode}, Exec={allow_exec}")

        if effective_mode == "local":
            return "local"

        if effective_mode == "cloud":
            if not settings.CLOUD_API_KEY:
                logger.warning("Cloud mode requested but no API Key found. Falling back to local.")
                return "local"
            return "cloud"

        # Auto Logic
        # 1. EXEC implies local (security & control)
        if allow_exec or self._is_exec_request(prompt):
            logger.info("Auto-Routing: EXEC detected -> LOCAL")
            return "local"

        # 2. Sensitive Data (Simplistic regex for now)
        if self._is_sensitive(prompt):
            logger.info("Auto-Routing: Sensitive Data detected -> LOCAL")
            return "local"

        # 3. Cloud (if key exists)
        if settings.CLOUD_API_KEY:
            # Heuristic: complex queries or web retrieval needs might go to cloud
            # For now, default fallback if key exists could be cloud for "better" reasoning IF strictly needed
            # But prompt says Default -> Local.
            # "3) طلب web/حديث + مفتاح cloud موجود → cloud"
            if self._needs_cloud_capabilities(prompt):
                logger.info("Auto-Routing: Cloud Capabilities needed -> CLOUD")
                return "cloud"

        # 4. Default -> Local
        logger.info("Auto-Routing: Default -> LOCAL")
        return "local"

    def _is_exec_request(self, prompt: str) -> bool:
        keywords = ["exec", "execution", "python code", "run this", "calculate"]
        return any(k in prompt.lower() for k in keywords)

    def _is_sensitive(self, prompt: str) -> bool:
        keywords = ["password", "secret", "private key", "ssn", "credit card"]
        return any(k in prompt.lower() for k in keywords)

    def _needs_cloud_capabilities(self, prompt: str) -> bool:
        keywords = ["latest news", "search web", "current events", "weather"]
        return any(k in prompt.lower() for k in keywords)
