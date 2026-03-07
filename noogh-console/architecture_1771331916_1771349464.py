from abc import ABC, abstractmethod

class GPUInfoStrategy(ABC):
    @abstractmethod
    def get_gpu_info(self):
        pass

class DefaultGPUInfoStrategy(GPUInfoStrategy):
    def get_gpu_info(self):
        # Default method to retrieve GPU info
        return {"model": "Default GPU", "memory": "8GB"}

class AdvancedGPUInfoStrategy(GPUInfoStrategy):
    def get_gpu_info(self):
        # More advanced method to retrieve GPU info
        # This could involve querying specific hardware or software APIs
        return {"model": "Advanced GPU", "memory": "16GB"}

class GPUInfoContext:
    def __init__(self, strategy: GPUInfoStrategy):
        self._strategy = strategy

    @property
    def strategy(self):
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: GPUInfoStrategy):
        self._strategy = strategy

    def execute_strategy(self):
        result = self._strategy.get_gpu_info()
        print(f"Retrieved GPU Info: {result}")

# Usage Example
if __name__ == "__main__":
    context = GPUInfoContext(DefaultGPUInfoStrategy())
    context.execute_strategy()

    # Switching to another strategy
    context.strategy = AdvancedGPUInfoStrategy()
    context.execute_strategy()