# Register a strategy
StrategyRegistry.register("basic", BasicStrategy)

# Use the registry to create strategies
strategy = StrategyRegistry.get_strategy("basic", config=settings)