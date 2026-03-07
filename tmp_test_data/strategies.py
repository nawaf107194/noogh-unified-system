# tmp_test_data/strategies.py

from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def execute(self, data):
        pass

class ConcreteStrategyA(Strategy):
    def execute(self, data):
        # Implement specific algorithm
        print("Executing strategy A with data:", data)
        return f"Processed {data} by A"

class ConcreteStrategyB(Strategy):
    def execute(self, data):
        # Implement specific algorithm
        print("Executing strategy B with data:", data)
        return f"Processed {data} by B"

class Context:
    def __init__(self, strategy: Strategy):
        self._strategy = strategy

    @property
    def strategy(self):
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: Strategy):
        self._strategy = strategy

    def execute_strategy(self, data):
        return self._strategy.execute(data)

# Example usage
if __name__ == "__main__":
    context = Context(ConcreteStrategyA())
    result = context.execute_strategy("initial data")
    print(result)

    # Change strategy at runtime
    context.strategy = ConcreteStrategyB()
    result = context.execute_strategy("changed data")
    print(result)