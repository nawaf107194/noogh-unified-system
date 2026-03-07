import time
import os
import logging

import requests

from gateway.app.core.config import get_settings
from gateway.app.core.logging import get_logger

settings = get_settings()
logger = get_logger("remote_brain")


class RemoteBrainService:
    """
    Client for the remote Neural OS GPU service.
    Replaces LocalBrainService to enable GPU acceleration via delegation.
    """

    def __init__(self):
        from config.ports import PORTS
        self.neural_engine_url = os.getenv("NEURAL_ENGINE_URL", f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}")
        self.tokenizer = None  # Remote service handles tokenization
        self.model = "Remote: " + settings.BASE_MODEL_NAME
        logger.info(f"Initialized RemoteBrainService pointing to {self.neural_engine_url}")

    def generate(self, prompt: str, max_new_tokens: int = 128, temperature: float = 0.7, top_p: float = 0.9) -> str:
        """
        Generate text using the remote GPU-accelerated service.
        """
        start_time = time.time()

        # Payload for Noug Neural OS /api/v1/process
        payload = {
            "text": prompt,
            "context": {"max_new_tokens": max_new_tokens, "temperature": temperature, "top_p": top_p},
            "store_memory": False,  # Don't pollute memory with raw inference
        }

        headers = {
            "X-Internal-Token": settings.NOOGH_INTERNAL_TOKEN,  # Correct header
            "Content-Type": "application/json",
        }

        try:
            # Use correct endpoint
            response = requests.post(
                f"{self.neural_engine_url}/api/v1/process", json=payload, headers=headers, timeout=settings.EXEC_TIMEOUT * 4
            )
            response.raise_for_status()

            result = response.json()
            # Extract conclusion/text from ProcessResponse
            generated_text = result.get("conclusion", "")

            duration = time.time() - start_time
            logger.info(f"Remote Inference: {duration:.4f}s")

            return generated_text

        except requests.exceptions.RequestException as e:
            logger.error(f"Remote brain generation failed: {e}")
            return f"Error: Could not connect to Neural Engine at {self.neural_engine_url}"
