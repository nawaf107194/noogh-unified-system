from dataclasses import dataclass
from typing import Optional, Dict, Type

@dataclass
class ConfigDependencies:
    config_factory: Optional[Type] = None
    config_manager: Optional[Type] = None
    config: Optional[Type] = None

class DependencyInjector:
    _instance = None
    _dependencies: Dict[str, any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register_dependency(cls, service_id: str, implementation):
        cls._dependencies[service_id] = implementation

    @classmethod
    def get_dependency(cls, service_id: str):
        if service_id not in cls._dependencies:
            raise ValueError(f"Dependency {service_id} not registered")
        return cls._dependencies[service_id]

    @classmethod
    def configure(cls, dependencies: ConfigDependencies):
        if dependencies.config_factory:
            cls.register_dependency("config_factory", dependencies.config_factory())
        if dependencies.config_manager:
            cls.register_dependency("config_manager", dependencies.config_manager())
        if dependencies.config:
            cls.register_dependency("config", dependencies.config())