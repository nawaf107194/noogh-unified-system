from abc import ABC, abstractmethod
from typing import Type, Dict, Any

class BaseService(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

class ServiceFactory(ABC):
    @abstractmethod
    def create_service(self, service_type: Type[BaseService], config: Dict[str, Any]) -> BaseService:
        pass

class DefaultServiceFactory(ServiceFactory):
    def create_service(self, service_type: Type[BaseService], config: Dict[str, Any]) -> BaseService:
        # Add common initialization logic here
        service = service_type(**config)
        service.start()
        return service

# Usage example:
if __name__ == '__main__':
    from proto_generated.trading.market_service import MarketService
    factory = DefaultServiceFactory()
    market_service = factory.create_service(
        MarketService,
        {"data_source": "real_time", "update_interval": 1}
    )
    print("Market service created:", market_service)