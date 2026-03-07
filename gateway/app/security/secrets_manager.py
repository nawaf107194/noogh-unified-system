import os
from typing import Dict


class SecretsManagerError(Exception):
    """Exception raised for errors in the secrets management system."""



class SecretsManager:
    """
    Authoritative secrets management mechanism.
    Loads secrets from environment variables only and fails fast on missing keys.
    """

    REQUIRED_KEYS = [
        "NOOGH_ADMIN_TOKEN",
        "NOOGH_SERVICE_TOKEN",
        "NOOGH_READONLY_TOKEN",
        "NOOGH_INTERNAL_TOKEN",
        "NOOGH_JOB_SIGNING_SECRET",
        "NOOGH_DATA_DIR",
        "NOOGH_HOST",
        "NOOGH_PORT",
    ]

    OPTIONAL_KEYS = [
        "LOCAL_MODEL_NAME",
        "ROUTING_MODE",
        "CLOUD_API_KEY",
        "CLOUD_PROVIDER",
        "CLOUD_API_URL",
        "CLOUD_MODEL",
        "GEMINI_API_KEY",
        "REDIS_URL",
    ]

    @staticmethod
    def load() -> Dict[str, str]:
        """
        Reads required secrets from os.environ.
        Raises SecretsManagerError immediately if any key is missing.
        Returns a dictionary of secrets.
        """
        secrets = {}
        missing_keys = []

        # Load Required Keys
        for key in SecretsManager.REQUIRED_KEYS:
            if key in SecretsManager.OPTIONAL_KEYS:
                continue  # Skip if moved to optional
            value = os.environ.get(key)
            if value is None:
                missing_keys.append(key)
            else:
                secrets[key] = value

        # Load Optional Keys
        for key in SecretsManager.OPTIONAL_KEYS:
            value = os.environ.get(key)
            if value is not None:
                secrets[key] = value

        if missing_keys:
            raise SecretsManagerError(f"CRITICAL: Missing required environment variables: {', '.join(missing_keys)}")

        return secrets
