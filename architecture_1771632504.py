from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def execute(self, data):
        pass

class ConcreteStrategyA(Strategy):
    def execute(self, data):
        # Logic for strategy A
        return data * 2

class ConcreteStrategyB(Strategy):
    def execute(self, data):
        # Logic for strategy B
        return data + 10

class StrategyFactory:
    @staticmethod
    def get_strategy(strategy_type):
        if strategy_type == 'A':
            return ConcreteStrategyA()
        elif strategy_type == 'B':
            return ConcreteStrategyB()
        else:
            raise ValueError("Invalid strategy type")

# Usage example
strategy = StrategyFactory.get_strategy('A')
result = strategy.execute(5)
print(result)  # Output: 10