# 2) Centralized Configuration and Secrets
# This file is NOT allowed to read environment variables directly.
# It depends on the bootstrap performed in main.py.

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server config
    HOST: str = "127.0.0.1"
    PORT: int = 8001
    LOG_LEVEL: str = "INFO"
    ENV_MODE: str = "production"  # "development" or "production"

    BASE_MODEL_NAME: str = "/home/noogh/projects/noogh_unified_system/src/models/noogh_sovereign_7b_v1"
    LORA_PATH: str = "/home/noogh/projects/noogh_unified_system/src/models/noogh_sovereign_7b_v1"  # LoRA on Qwen2.5-7B-Instruct
    NOOGH_EMPTY_CACHE: int = 1
    DEVICE: str = "cuda"
    NEURAL_SERVICE_URL: str = ""
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CLUSTER_NODES: str = ""  # Comma-separated list of host:port for Cluster mode

    ROUTING_MODE: str = "auto"

    # Cloud Configuration (Placeholders, will be overridden by DI)
    CLOUD_API_KEY: str = ""
    CLOUD_API_URL: str = "https://api.openai.com/v1/chat/completions"
    CLOUD_MODEL: str = "gpt-3.5-turbo"
    CLOUD_PROVIDER: str = "openai"
    GEMINI_API_KEY: str = ""

    # Security Settings
    ALLOW_EXEC: bool = True
    EXEC_TIMEOUT: int = 5
    INFERENCE_TIMEOUT: int = 30
    NOOGH_ADMIN_TOKEN: str = ""
    NOOGH_SERVICE_TOKEN: str = ""
    NOOGH_READONLY_TOKEN: str = ""
    NOOGH_INTERNAL_TOKEN: str = ""

    # Internal Security
    NOOGH_JOB_SIGNING_SECRET: str = ""

    # Session Settings
    SESSION_ENABLED: bool = True
    SESSION_MAX_HISTORY: int = 10

    # CORS Settings
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8001"]

    model_config = {"env_file": None, "extra": "ignore"}  # Disable direct env loading


@lru_cache()
def get_settings():
    return Settings()
