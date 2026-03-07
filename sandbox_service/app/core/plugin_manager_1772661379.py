from typing import Protocol, Dict, Type
from .models import SandboxConfig

class SandboxStrategy(Protocol):
    """Common interface for all sandbox strategies"""
    def execute(self, config: SandboxConfig) -> Dict:
        """Execute the sandbox strategy"""
        ...

class StrategyFactory:
    """Factory for creating different sandbox strategies"""
    _strategies: Dict[str, Type[SandboxStrategy]] = {}

    @classmethod
    def register(cls, name: str) -> callable:
        """Register a new strategy"""
        def decorator(strategy: Type[SandboxStrategy]) -> Type[SandboxStrategy]:
            cls._strategies[name] = strategy
            return strategy
        return decorator

    @classmethod
    def create_strategy(cls, name: str, config: SandboxConfig) -> SandboxStrategy:
        """Create a strategy instance"""
        if name not in cls._strategies:
            raise ValueError(f"Strategy {name} not registered")
        return cls._strategies[name]()

class BaseSandboxStrategy:
    """Base implementation for sandbox strategies"""
    def __init__(self):
        self.config = None

    def set_config(self, config: SandboxConfig):
        """Set the configuration for this strategy"""
        self.config = config

    def execute(self, config: SandboxConfig) -> Dict:
        """Execute the strategy with given config"""
        raise NotImplementedError