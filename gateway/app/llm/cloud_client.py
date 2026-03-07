from typing import Dict

import httpx

from gateway.app.core.config import get_settings
from gateway.app.core.logging import get_logger

settings = get_settings()
logger = get_logger("cloud_client")


class CloudClient:
    """Client for cloud inference APIs (OpenAI, Anthropic, etc.)"""

    def __init__(self, secrets: Dict[str, str]):
        self.settings = get_settings()
        self.secrets = secrets
        self.client = httpx.Client(timeout=120.0)

    def generate(self, prompt: str, max_new_tokens: int = 500, timeout: float = None, **kwargs) -> str:
        """Call cloud API for inference (Synchronous)"""
        api_key = self.secrets.get("CLOUD_API_KEY")
        provider = self.secrets.get("CLOUD_PROVIDER", "").lower()

        if not api_key:
            return "[Error: Cloud API key not configured]"

        if provider in ["openai", "deepseek"]:
            return self._openai_generate(prompt, api_key, provider, max_new_tokens, timeout)
        else:
            return f"[Error: Unsupported provider '{provider}']"

    def _openai_generate(self, prompt: str, api_key: str, provider: str, max_tokens: int, timeout: float = None) -> str:
        """OpenAI-compatible API call"""
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        # Adjust URL for deepseek if needed (handled by env var CLOUD_API_URL)

        payload = {
            "model": self.settings.CLOUD_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        try:
            response = self.client.post(self.settings.CLOUD_API_URL, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            logger.error(f"Cloud API error: {e}")
            if hasattr(e, "response") and e.response is not None:
                return f"[Error: Cloud API failed ({e.response.status_code}) - {e.response.text}]"
            return f"[Error: Cloud API failed - {str(e)}]"
        except KeyError as e:
            logger.error(f"Unexpected response format: {e}")
            return "[Error: Unexpected cloud response format]"

    def close(self):
        """Close HTTP client"""
        self.client.close()
