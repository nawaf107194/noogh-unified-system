from .service_factory import ServiceFactory
from .service_registry import ServiceRegistry
from .service_discovery import ServiceDiscovery

class ServiceMediator:
    def __init__(self):
        self.factory = ServiceFactory()
        self.registry = ServiceRegistry()
        self.discovery = ServiceDiscovery()
        
    def register_service(self, service_name, service_class):
        service_instance = self.factory.create_service(service_class)
        self.registry.register(service_name, service_instance)
        self.discovery.publish(service_name)
        
    def get_service(self, service_name):
        if not self.discovery.is_available(service_name):
            raise ValueError(f"Service {service_name} not available")
        return self.registry.get(service_name)