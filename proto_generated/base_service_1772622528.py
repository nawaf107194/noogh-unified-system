# proto_generated/base_service.py

class BaseService:
    def __init__(self, service_name):
        self.service_name = service_name

class ServiceFactory:
    _services = {}

    @staticmethod
    def register_service(service_name, service_class):
        ServiceFactory._services[service_name] = service_class

    @staticmethod
    def create_service(service_name, *args, **kwargs):
        if service_name not in ServiceFactory._services:
            raise ValueError(f"Service {service_name} not registered")
        
        service_class = ServiceFactory._services[service_name]
        return service_class(*args, **kwargs)

# Example service implementation
class MarketService(BaseService):
    def __init__(self, service_name="market"):
        super().__init__(service_name)
    
    @classmethod
    def get_service(cls):
        return cls()

# Registration would happen in service_registry.py
# ServiceFactory.register_service("market", MarketService)