from typing import Dict, Type, Optional

class ConfigRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._configs = {}
        return cls._instance

    def register_config(self, config_name: str, config_class: Type) -> None:
        """Register a new configuration type"""
        self._configs[config_name] = config_class

    def unregister_config(self, config_name: str) -> None:
        """Remove a registered configuration"""
        if config_name in self._configs:
            del self._configs[config_name]

    def get_config(self, config_name: str, **kwargs) -> Optional[object]:
        """Retrieve and instantiate a registered configuration"""
        if config_name in self._configs:
            return self._configs[config_name](**kwargs)
        return None

    def get_registered_configs(self) -> Dict[str, Type]:
        """Get all registered configuration classes"""
        return self._configs.copy()