from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """Base interface for all strategies"""
    
    def __init__(self, config):
        self.config = config
        
    @abstractmethod
    def execute(self, data):
        """Execute the strategy on given data"""
        pass
    
    def validate_config(self):
        """Validate strategy configuration"""
        pass
    
    def get_metrics(self):
        """Return performance metrics"""
        return {}