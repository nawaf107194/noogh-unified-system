from abc import ABC, abstractmethod

class TradingStrategy(ABC):
    """Abstract base class for trading strategies."""

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def generate_signal(self, data):
        """Generate trading signal based on input data."""
        pass

    @abstractmethod
    def validate(self):
        """Validate strategy configuration."""
        pass

    def get_parameters(self):
        """Return strategy parameters."""
        return self.config