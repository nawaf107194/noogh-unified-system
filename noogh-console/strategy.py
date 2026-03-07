from .strategy import ServiceStrategy, DefaultServiceStrategy

class ServiceManager:
    def __init__(self, strategy: ServiceStrategy = DefaultServiceStrategy()):
        self.strategy = strategy
        
    def create_service(self, service_type, config):
        return self.strategy.create_service(service_type, config)