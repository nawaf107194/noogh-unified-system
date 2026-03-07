class ServiceLocator:
    def __init__(self):
        self.services = {}
        
    def register_service(self, service_key, service_instance):
        self.services[service_key] = service_instance
        
    def get_service(self, service_key):
        if service_key not in self.services:
            raise ValueError(f"Service {service_key} not registered")
        return self.services[service_key]

class ServiceRegistry:
    def __init__(self):
        self.locator = ServiceLocator()
        
    def __call__(self, service_key):
        return self.locator.get_service(service_key)

SERVICE_REGISTRY = ServiceRegistry()