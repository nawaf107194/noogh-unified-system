# reports/config_manager.py

from typing import Dict, Any

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._config_data: Dict[str, Any] = {}
        return cls._instance

    @classmethod
    def load_config(cls, config_file_path: str):
        # Implement logic to load configuration from a file
        pass

    @classmethod
    def get_config(cls, key: str) -> Any:
        # Implement logic to retrieve a specific configuration value
        pass

    @classmethod
    def set_config(cls, key: str, value: Any):
        # Implement logic to update a specific configuration value
        cls._config_data[key] = value

# Usage example in test_config_manager.py
if __name__ == '__main__':
    config_manager = ConfigManager()
    config_manager.load_config('path/to/config/file')
    print(config_manager.get_config('key'))
    config_manager.set_config('key', 'new_value')