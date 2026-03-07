import os
import json
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config_data = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Loads the configuration from the specified path."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file at {self.config_path} does not exist.")
        
        with open(self.config_path, 'r') as file:
            return json.load(file)

    def get_config(self, section: str, key: str) -> Any:
        """Retrieves a configuration value by section and key."""
        if section in self.config_data and key in self.config_data[section]:
            return self.config_data[section][key]
        else:
            raise KeyError(f"Key '{key}' not found in section '{section}'.")

    def validate_config(self, required_sections: Dict[str, Dict[str, type]]) -> None:
        """Validates the configuration against required sections and types."""
        for section, keys in required_sections.items():
            if section not in self.config_data:
                raise ValueError(f"Section '{section}' is missing in the configuration.")
            
            for key, expected_type in keys.items():
                if key not in self.config_data[section]:
                    raise ValueError(f"Key '{key}' is missing in section '{section}'.")
                
                actual_type = type(self.config_data[section][key])
                if actual_type != expected_type:
                    raise TypeError(f"Type mismatch for key '{key}' in section '{section}'. Expected {expected_type}, got {actual_type}.")

# Example usage
if __name__ == "__main__":
    config_path = "path/to/config.json"
    config_manager = ConfigManager(config_path)
    
    # Example validation
    required_sections = {
        "database": {"host": str, "port": int},
        "security": {"enabled": bool}
    }
    config_manager.validate_config(required_sections)
    
    # Retrieve a configuration value
    db_host = config_manager.get_config("database", "host")
    print(f"Database host: {db_host}")