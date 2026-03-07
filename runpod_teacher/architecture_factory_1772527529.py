from abc import ABC, abstractmethod
from typing import Dict, Any
from unified_core.core.config_manager import ConfigManager

class ArchitectureStrategy(ABC):
    """Abstract base class for architecture strategies"""
    
    @abstractmethod
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data according to the architecture strategy"""
        pass
    
    @abstractmethod
    def get_response(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final response from processed data"""
        pass

class ArchitectureFactory:
    """Factory class for creating architecture strategy instances"""
    
    def __init__(self):
        self._strategies = {}
        self.config = ConfigManager()
        
    def register_strategy(self, name: str, strategy: ArchitectureStrategy):
        """Register a new architecture strategy"""
        self._strategies[name] = strategy
        
    def get_strategy(self) -> ArchitectureStrategy:
        """Get the current architecture strategy based on configuration"""
        strategy_name = self.config.get('architecture_strategy', 'default')
        return self._strategies.get(strategy_name, self._strategies['default'])