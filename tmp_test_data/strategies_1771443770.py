from abc import ABC, abstractmethod

class ProcessingStrategy(ABC):
    @abstractmethod
    def process(self, data):
        pass

class SimpleProcessingStrategy(ProcessingStrategy):
    def process(self, data):
        # Example simple processing
        return data.upper()

class ComplexProcessingStrategy(ProcessingStrategy):
    def process(self, data):
        # Example complex processing
        return data.lower()

class Processor:
    def __init__(self, strategy: ProcessingStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: ProcessingStrategy):
        self._strategy = strategy

    def execute(self, data):
        result = self._strategy.process(data)
        print(f"Processed data: {result}")

# Usage example
if __name__ == "__main__":
    processor = Processor(SimpleProcessingStrategy())
    processor.execute("Hello World")

    # Switching to another strategy
    processor.set_strategy(ComplexProcessingStrategy())
    processor.execute("Hello World")