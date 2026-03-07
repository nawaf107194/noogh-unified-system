# proto_generated/service_factory.py

from .service_registry import ServiceRegistry
from .base_service import BaseService
from .services_pb2_grpc import *
from .common.types_pb2 import *
from .trading.market_pb2 import *
from .cognitive.intelligence_pb2 import *

class ServiceFactory:
    _instance = None
    _registry = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._registry = ServiceRegistry()
        return cls._instance

    def create_service(self, service_type, service_name=None):
        """
        Creates and registers a new service instance
        """
        if service_type not in self._get_valid_service_types():
            raise ValueError(f"Invalid service type: {service_type}")

        # Create base service instance
        service = BaseService(service_name or service_type)
        
        # Configure service based on type
        if service_type == "trading":
            service_pb2 = market_pb2
            service_pb2_grpc = market_pb2_grpc
        elif service_type == "common":
            service_pb2 = types_pb2
            service_pb2_grpc = types_pb2_grpc
        elif service_type == "cognitive":
            service_pb2 = intelligence_pb2
            service_pb2_grpc = intelligence_pb2_grpc
        else:
            raise ValueError("Unsupported service type")

        # Initialize gRPC components
        service.add_grpc_server(service_pb2, service_pb2_grpc)
        
        # Register service
        self._registry.register_service(service_name or service_type, service)
        
        return service

    def _get_valid_service_types(self):
        return ["trading", "common", "cognitive"]

# Usage example
if __name__ == '__main__':
    factory = ServiceFactory()
    trading_service = factory.create_service("trading", "market_service")