# reports/config_manager.py

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._configurations = {}
        return cls._instance

    def load_configuration(self, config_name, data_source):
        # Load configuration from a data source
        self._configurations[config_name] = data_source.load_config(config_name)

    def get_configuration(self, config_name):
        # Retrieve configuration by name
        if config_name not in self._configurations:
            raise ValueError(f"Configuration '{config_name}' not found")
        return self._configurations[config_name]

# Example usage in config_1771674446.py and config.py

from reports.config_manager import ConfigManager

config_manager = ConfigManager()

# Load configuration
config_manager.load_configuration('default', data_source)

# Get configuration
config = config_manager.get_configuration('default')