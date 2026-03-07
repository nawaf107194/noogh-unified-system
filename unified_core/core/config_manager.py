import json
import os
from typing import Any, Dict, Optional
try:
    import yaml
except ImportError:
    yaml = None

class ConfigManager:
    """
    Centralized Configuration Manager for the NOOGH Unified System.
    Implements a Singleton pattern to ensure a consistent configuration state.
    Supports JSON and YAML (if available).
    """
    _instance: Optional['ConfigManager'] = None
    _config: Dict[str, Any] = {}
    _loaded_from: Optional[str] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def get_instance() -> 'ConfigManager':
        """Get the singleton instance (for backward compatibility)."""
        if ConfigManager._instance is None:
            ConfigManager()
        return ConfigManager._instance

    def load_config(self, config_path: str, merge: bool = True) -> bool:
        """
        Load configuration from a JSON or YAML file.
        :param config_path: Path to the configuration file.
        :param merge: If True, merge with existing config; otherwise, replace it.
        :return: True if successful, False otherwise.
        """
        if not os.path.exists(config_path):
            return False

        try:
            with open(config_path, 'r') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    if yaml:
                        new_data = yaml.safe_load(f)
                    else:
                        raise ImportError("PyYAML is not installed. Cannot load YAML config.")
                else:
                    new_data = json.load(f)

            if merge:
                self._config.update(new_data or {})
            else:
                self._config = new_data or {}
            
            self._loaded_from = config_path
            return True
        except Exception as e:
            print(f"Error loading config from {config_path}: {e}")
            return False

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a setting value. Supports nested keys with dot notation (e.g., 'trading.leverage').
        """
        parts = key.split('.')
        val = self._config
        for part in parts:
            if isinstance(val, dict) and part in val:
                val = val[part]
            else:
                return default
        return val

    def set_setting(self, key: str, value: Any):
        """
        Set a setting value. Supports nested keys with dot notation.
        """
        parts = key.split('.')
        target = self._config
        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value

    def save_config(self, config_path: Optional[str] = None) -> bool:
        """
        Save the current configuration to a file.
        """
        path = config_path or self._loaded_from
        if not path:
            return False

        try:
            with open(path, 'w') as f:
                if path.endswith('.yaml') or path.endswith('.yml'):
                    if yaml:
                        yaml.safe_dump(self._config, f, default_flow_style=False)
                    else:
                        raise ImportError("PyYAML is not installed. Cannot save YAML config.")
                else:
                    json.dump(self._config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config to {path}: {e}")
            return False

    def clear(self):
        """Reset the configuration."""
        self._config = {}
        self._loaded_from = None

    @property
    def config(self) -> Dict[str, Any]:
        return self._config.copy()
