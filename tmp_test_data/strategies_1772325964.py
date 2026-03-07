from abc import ABC, abstractmethod

class DataProcessingStrategy(ABC):
    @abstractmethod
    def process(self, data):
        pass

class FilterStrategy(DataProcessingStrategy):
    def process(self, data):
        # Implement filtering logic here
        return [item for item in data if item % 2 == 0]

class TransformStrategy(DataProcessingStrategy):
    def process(self, data):
        # Implement transformation logic here
        return [item * 2 for item in data]

class DataProcessor:
    def __init__(self, strategy: DataProcessingStrategy):
        self.strategy = strategy

    def set_strategy(self, strategy: DataProcessingStrategy):
        self.strategy = strategy

    def process_data(self, data):
        return self.strategy.process(data)

# Example usage
if __name__ == '__main__':
    data = [1, 2, 3, 4, 5]

    filter_strategy = FilterStrategy()
    processor = DataProcessor(filter_strategy)
    filtered_data = processor.process_data(data)
    print("Filtered Data:", filtered_data)

    transform_strategy = TransformStrategy()
    processor.set_strategy(transform_strategy)
    transformed_data = processor.process_data(data)
    print("Transformed Data:", transformed_data)