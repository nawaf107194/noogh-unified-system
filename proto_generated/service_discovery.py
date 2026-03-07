# proto_generated/service_discovery.py
class ServiceDiscovery:
    _instance = None
    _services = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register_service(cls, service_name, service_class):
        cls._services[service_name] = service_class

    @classmethod
    def discover_service(cls, service_name):
        service_class = cls._services.get(service_name)
        if not service_class:
            raise ValueError(f"Service {service_name} not registered")
        return service_class()

    @classmethod
    def get_registered_services(cls):
        return list(cls._services.keys())