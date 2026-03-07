# tmp_test_data/strategies.py

from abc import ABC, abstractmethod
from typing import Dict, Type

class Strategy(ABC):
    @abstractmethod
    def execute(self) -> None:
        pass

class BuyStrategy(Strategy):
    def execute(self) -> None:
        print("Executing buy strategy")

class SellStrategy(Strategy):
    def execute(self) -> None:
        print("Executing sell strategy")

class StrategyFactory:
    strategies: Dict[str, Type[Strategy]] = {
        "buy": BuyStrategy,
        "sell": SellStrategy
    }

    @staticmethod
    def get_strategy(strategy_type: str) -> Strategy:
        if strategy_type not in StrategyFactory.strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        return StrategyFactory.strategies[strategy_type]()

# Example usage
if __name__ == '__main__':
    strategy_type = "buy"
    strategy = StrategyFactory.get_strategy(strategy_type)
    strategy.execute()