# reports/dependency_container.py

class DependencyContainer:
    def __init__(self):
        self._registry = {}
    
    def register(self, service_id, service_class, *args, **kwargs):
        self._registry[service_id] = {
            'class': service_class,
            'args': args,
            'kwargs': kwargs
        }
    
    def get(self, service_id):
        if service_id not in self._registry:
            raise ValueError(f"Service {service_id} not registered")
        
        service_info = self._registry[service_id]
        return service_info['class'](*service_info['args'], **service_info['kwargs'])
    
    def has(self, service_id):
        return service_id in self._registry

# Usage example in other files:
# from reports.dependency_container import DependencyContainer
# container = DependencyContainer()
# container.register('config_manager', reports.config_manager.ConfigManager)
# config_manager = container.get('config_manager')