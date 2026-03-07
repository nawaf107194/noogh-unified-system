# config/config_loader.py

import json
from typing import Dict
from .settings import Settings
from .ports import Ports
from .integrity import IntegrityChecker

class ConfigurationLoader:
    def __init__(self):
        self.settings = None
        self.ports = None
        self.integrity_checker = None

    def load_config(self, config_path: str) -> None:
        """Load and validate the configuration from a JSON file."""
        with open(config_path, 'r') as file:
            config_data = json.load(file)
        
        # Load settings
        self.settings = Settings.from_dict(config_data.get('settings', {}))
        
        # Load ports
        self.ports = Ports.from_dict(config_data.get('ports', {}))
        
        # Validate integrity
        self.integrity_checker = IntegrityChecker()
        if not self.integrity_checker.validate(self.settings, self.ports):
            raise ValueError("Configuration integrity check failed.")
    
    def get_settings(self) -> Settings:
        """Return the loaded settings."""
        return self.settings
    
    def get_ports(self) -> Ports:
        """Return the loaded ports."""
        return self.ports