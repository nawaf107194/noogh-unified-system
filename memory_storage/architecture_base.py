from abc import ABC, abstractmethod
from memory_storage.strategies.storage_strategy import StorageStrategy

class BaseArchitecture(ABC):
    def __init__(self, strategy: StorageStrategy):
        self.strategy = strategy
        self._initialize_storage()

    @abstractmethod
    def _initialize_storage(self):
        """Initialize storage connection and configurations"""
        pass

    def save(self, data):
        return self.strategy.save(data)

    def retrieve(self, key):
        return self.strategy.retrieve(key)

    def delete(self, key):
        return self.strategy.delete(key)

    def get_stats(self):
        return self.strategy.get_stats()

    def _validate_data(self, data):
        """Basic data validation"""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        return data

    def _log_operation(self, operation_type, data=None):
        """Log storage operations"""
        # Implementation would connect to real logging system
        pass