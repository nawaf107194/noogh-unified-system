# config/config_strategy.py

from abc import ABC, abstractmethod

class ConfigStrategy(ABC):
    """Base class for configuration strategies"""
    
    @abstractmethod
    def load(self, config_path: str) -> dict:
        """Load configuration from a source"""
        pass
    
    @abstractmethod
    def save(self, config_path: str, config_data: dict) -> None:
        """Save configuration to a source"""
        pass

class FileConfigStrategy(ConfigStrategy):
    """Strategy for handling file-based configurations"""
    
    def load(self, config_path: str) -> dict:
        # Implement file loading logic
        pass
    
    def save(self, config_path: str, config_data: dict) -> None:
        # Implement file saving logic
        pass

class DatabaseConfigStrategy(ConfigStrategy):
    """Strategy for handling database-based configurations"""
    
    def load(self, config_path: str) -> dict:
        # Implement database query logic
        pass
    
    def save(self, config_path: str, config_data: dict) -> None:
        # Implement database update logic
        pass