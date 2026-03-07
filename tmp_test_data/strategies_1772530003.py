from typing import Protocol, Dict, Type

class Strategy(Protocol):
    def execute(self) -> None:
        """Execute the strategy's specific logic"""
        ...

class StrategyFactory:
    _strategies: Dict[str, Type[Strategy]] = {}
    
    @classmethod
    def register(cls, name: str) -> callable:
        """Register a strategy class with the factory"""
        def decorator(strategy_class: Type[Strategy]) -> Type[Strategy]:
            cls._strategies[name] = strategy_class
            return strategy_class
        return decorator
    
    @classmethod
    def create_strategy(cls, name: str, **kwargs) -> Strategy:
        """Create a strategy instance by name"""
        strategy_class = cls._strategies.get(name)
        if not strategy_class:
            raise ValueError(f"Strategy '{name}' not registered")
        return strategy_class(**kwargs)

# Example usage:
# 
# @StrategyFactory.register("concrete_strategy")
# class ConcreteStrategy:
#     def __init__(self, **kwargs):
#         self.param = kwargs.get("param", "default")
#     
#     def execute(self):
#         print(f"Executing with param: {self.param}")
# 
# if __name__ == "__main__":
#     strategy = StrategyFactory.create_strategy("concrete_strategy", param="value")
#     strategy.execute()