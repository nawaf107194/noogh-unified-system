# proto_generated/service_registry.py

class ServiceRegistry:
    _instance = None
    _services = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, service_name, service_class):
        cls._services[service_name] = service_class
    
    @classmethod
    def get_service(cls, service_name, *args, **kwargs):
        if service_name not in cls._services:
            raise ValueError(f"Service '{service_name}' not registered")
        
        service_class = cls._services[service_name]
        return service_class(*args, **kwargs)

# proto_generated/__init__.py
from .service_registry import ServiceRegistry
from .base_service import BaseService
from .trading.market_pb2_grpc import MarketService
from .cognitive.intelligence_pb2_grpc import IntelligenceService
from .evolution.learning_pb2 import LearningService

# Register available services
ServiceRegistry.register("market", MarketService)
ServiceRegistry.register("intelligence", IntelligenceService)
ServiceRegistry.register("learning", LearningService)

# proto_generated/base_service.py
class BaseService:
    def __init__(self, service_name):
        self.service_name = service_name