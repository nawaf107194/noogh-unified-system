from abc import ABC, abstractmethod
from typing import Dict, Any
from neurons.data_router import DataRouter

class FilterStrategy(ABC):
    """Abstract base class for filter strategies"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_router = DataRouter()
        
    @abstractmethod
    def apply_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the filter logic to the input data"""
        pass
    
    def _get_common_data(self) -> Dict[str, Any]:
        """Get common data used by multiple filters"""
        return self.data_router.get_common_data()
    
class LongFilterStrategy(FilterStrategy):
    """Long filter implementation"""
    
    def apply_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Implement long filter logic
        common_data = self._get_common_data()
        return {**data, **common_data}

class ShortFilterStrategy(FilterStrategy):
    """Short filter implementation"""
    
    def apply_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Implement short filter logic
        common_data = self._get_common_data()
        return {**data, **common_data}

class FilterContext:
    """Context class to manage filter strategies"""
    
    def __init__(self, strategy: FilterStrategy):
        self.strategy = strategy
        
    def execute_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the selected filter strategy"""
        return self.strategy.apply_filter(data)