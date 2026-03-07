import os
import json
import re
from typing import Dict, List, Any

class ConfigValidator:
    def __init__(self, config_files: List[str]):
        self.config_files = config_files
        self.configurations = {}

    def load_configs(self) -> None:
        """Loads configurations from specified files."""
        for file in self.config_files:
            if os.path.exists(file):
                with open(file, 'r') as f:
                    try:
                        self.configurations[file] = json.load(f)
                    except json.JSONDecodeError as e:
                        print(f"Failed to decode JSON from {file}: {e}")
            else:
                print(f"Config file not found: {file}")

    def validate_configs(self) -> bool:
        """Validates configurations based on predefined rules."""
        all_valid = True
        for file, config in self.configurations.items():
            if not self.validate_config(config):
                all_valid = False
                print(f"Validation failed for {file}")
        return all_valid

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Applies validation rules to a single configuration dictionary."""
        # Example validation rules
        required_keys = ['host', 'port', 'timeout']
        for key in required_keys:
            if key not in config:
                print(f"Missing required key '{key}'")
                return False
        
        if not isinstance(config.get('port'), int):
            print(f"'port' must be an integer")
            return False
        
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', str(config.get('host'))):
            print(f"'host' must be a valid IP address")
            return False
        
        if config.get('timeout') < 0:
            print(f"'timeout' must be a non-negative value")
            return False
        
        return True

# Usage example
if __name__ == "__main__":
    validator = ConfigValidator([
        "config/settings.json",
        "gateway/app/analytics/config.json"
    ])
    validator.load_configs()
    if validator.validate_configs():
        print("All configurations are valid.")
    else:
        print("Some configurations are invalid.")