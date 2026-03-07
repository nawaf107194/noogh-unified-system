from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseFilterStrategy(ABC):
    """Base class for all filter strategies"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
    @abstractmethod
    def filter(self, data: Any) -> Any:
        """Apply the filter to the input data"""
        pass
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'BaseFilterStrategy':
        """Create strategy instance from configuration"""
        return cls(config)
    
class FilterStrategyFactory:
    """Factory for creating filter strategy instances"""
    
    @staticmethod
    def create_strategy(strategy_name: str, config: Dict[str, Any]) -> BaseFilterStrategy:
        """
        Create a filter strategy instance by name
        Args:
            strategy_name: Name of the strategy to create
            config: Configuration for the strategy
        Returns:
            Filter strategy instance
        Raises:
            ValueError: If strategy name is not recognized
        """
        strategy_classes = {
            'basic': BasicFilterStrategy,
            'advanced': AdvancedFilterStrategy
        }
        
        strategy_class = strategy_classes.get(strategy_name)
        if not strategy_class:
            raise ValueError(f"Unknown filter strategy: {strategy_name}")
            
        return strategy_class(config)