import json
from typing import Any

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            # Initialize with default settings
            cls._instance.settings = {}
        return cls._instance

    def load_config(self, config_path: str) -> None:
        """ Load configuration from a JSON file """
        with open(config_path, 'r') as f:
            self.settings = json.load(f)

    def get_setting(self, key: str, default_value: Any = None) -> Any:
        """ Get a setting value by key """
        return self.settings.get(key, default_value)

    def set_setting(self, key: str, value: Any) -> None:
        """ Set a setting value by key """
        self.settings[key] = value

# Example usage
if __name__ == "__main__":
    config_manager = ConfigManager()
    config_manager.load_config('config.json')
    print(config_manager.get_setting('database_url', 'default_url'))
    config_manager.set_setting('debug_mode', True)