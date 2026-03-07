from typing import Dict, Type, Callable

class ServiceManager:
    def __init__(self):
        self._services: Dict[Type, Callable] = {}
        self._instances: Dict[Type, object] = {}

    def register_service(self, service_type: Type, factory: Callable):
        self._services[service_type] = factory

    def get_service(self, service_type: Type):
        if service_type not in self._services:
            raise ValueError(f"Service {service_type} not registered")
        
        if service_type not in self._instances:
            self._instances[service_type] = self._services[service_type]()
        
        return self._instances[service_type]

    def reset_service(self, service_type: Type):
        if service_type in self._instances:
            del self._instances[service_type]

# Update existing service classes to use the ServiceManager
# Example modification in service_factory.py:
"""
from .service_manager import service_manager

class BaseServiceFactory:
    def __init__(self):
        service_manager.register_service(self.__class__, self.__class__)
    
    @classmethod
    def get_instance(cls):
        return service_manager.get_service(cls)
"""