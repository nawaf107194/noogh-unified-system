# memory_storage/strategies/storage_strategy.py

class StorageStrategy:
    def __init__(self):
        self.strategies = {}

    def register(self, name: str, strategy) -> None:
        if name in self.strategies:
            raise ValueError(f"Strategy '{name}' already registered.")
        self.strategies[name] = strategy

    def get_strategy(self, name: str):
        if name not in self.strategies:
            raise KeyError(f"Strategy '{name}' is not registered.")
        return self.strategies[name]

# Usage example
if __name__ == "__main__":
    from memory_storage.strategies.concrete_strategy_a import ConcreteStrategyA
    from memory_storage.strategies.concrete_strategy_b import ConcreteStrategyB

    strategy_registry = StorageStrategy()
    strategy_registry.register("strategy_a", ConcreteStrategyA())
    strategy_registry.register("strategy_b", ConcreteStrategyB())

    # Retrieve strategies as needed
    strategy_a = strategy_registry.get_strategy("strategy_a")
    strategy_b = strategy_registry.get_strategy("strategy_b")

    # Example usage of the retrieved strategies
    strategy_a.execute()
    strategy_b.execute()