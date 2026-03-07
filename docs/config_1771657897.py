from typing import Dict

class ConfigManager:
    _config: Dict[str, any] = {}

    def __enter__(self):
        # Load configuration here (e.g., from a file or environment variables)
        self._config = {'key': 'value'}
        return self._config

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up resources if needed
        pass

def get_config() -> dict:
    with ConfigManager() as config:
        return config