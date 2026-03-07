# noogh/utils/config_manager.py

from typing import Dict, Any

class ConfigManager:
    _instances = {}

    @staticmethod
    def get_instance(config_type: str) -> 'ConfigManager':
        if config_type not in ConfigManager._instances:
            ConfigManager._instances[config_type] = ConfigManager()
        return ConfigManager._instances[config_type]

    def __init__(self):
        self.configs = {}

    def load_config(self, config_file: str) -> None:
        # Load configuration from file
        pass

    def get_config(self, key: str) -> Any:
        return self.configs.get(key)

# Usage example in another module
config_manager = ConfigManager.get_instance('default')
config_manager.load_config('default_config.json')
my_config = config_manager.get_config('my_key')