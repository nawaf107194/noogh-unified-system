import json
from typing import Any, Dict

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config = {}
        return cls._instance

    def load_config(self, config_path: str) -> None:
        """Load configuration from a JSON file."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)

    def get_config(self, key: str) -> Any:
        """Retrieve a configuration value by key."""
        return self.config.get(key)

    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value by key."""
        self.config[key] = value

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values at once."""
        self.config.update(updates)

# Example usage:
if __name__ == "__main__":
    config_manager = ConfigManager()
    config_manager.load_config('path_to_config.json')
    
    # Retrieve a configuration value
    model_path = config_manager.get_config('model_path')
    print(f"Model path: {model_path}")
    
    # Set a new configuration value
    config_manager.set_config('new_key', 'new_value')
    
    # Update multiple configuration values
    config_manager.update_config({'learning_rate': 0.01, 'batch_size': 32})