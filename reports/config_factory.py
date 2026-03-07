# reports/config_factory.py

from dataclasses import dataclass
from typing import Type, Optional
from unified_core.core.config_manager import ConfigManager
from reports.config import Config

@dataclass
class ConfigFactory:
    _instance: Optional['ConfigFactory'] = None
    _config_managers: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_config_manager(self, config_class: Type[Config] = Config) -> ConfigManager:
        """Get or create a config manager for the specified config class."""
        if config_class not in self._config_managers:
            self._config_managers[config_class] = ConfigManager(config_class)
        return self._config_managers[config_class]

    def create_config(self, config_class: Type[Config] = Config, **kwargs) -> Config:
        """Create a new config instance with specified parameters."""
        return config_class(**kwargs)

# Usage example:
if __name__ == '__main__':
    from reports.config import DefaultConfig
    
    factory = ConfigFactory()
    config_manager = factory.get_config_manager(DefaultConfig)
    config = factory.create_config(DefaultConfig, param1='value1')
    print(config_manager.get_config())