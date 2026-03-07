from typing import Dict, Any
import json
import os

class ConfigurationManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config = {}
        return cls._instance

    def load_config(self, config_path: str) -> None:
        """Load configuration from file"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get configuration setting with optional default"""
        return self.config.get(key, default)

    @staticmethod
    def get_instance() -> 'ConfigurationManager':
        """Get singleton instance"""
        if not ConfigurationManager._instance:
            ConfigurationManager()
        return ConfigurationManager._instance