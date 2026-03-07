# proto_generated/service_manager.py

from .service_factory import ServiceFactory
from .service_registry import ServiceRegistry
from .base_service import BaseService

class ServiceManager:
    def __init__(self):
        self.factory = ServiceFactory()
        self.registry = ServiceRegistry()

    def create_and_register_service(self, service_type, *args, **kwargs):
        """Create service instance and register it in one step"""
        service = self.factory.create_service(service_type, *args, **kwargs)
        if isinstance(service, BaseService):
            self.registry.register_service(service)
            return service
        raise ValueError("Invalid service type or implementation")

    def get_service(self, service_id):
        """Retrieve service by ID from registry"""
        return self.registry.get_service(service_id)

    def list_services(self):
        """List all registered services"""
        return self.registry.list_services()

    def shutdown_service(self, service_id):
        """Gracefully shutdown service and remove from registry"""
        service = self.get_service(service_id)
        if service:
            service.shutdown()
            self.registry.unregister_service(service_id)
            return True
        return False