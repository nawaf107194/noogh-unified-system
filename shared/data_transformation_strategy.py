from abc import ABC, abstractmethod

class DataTransformationStrategy(ABC):
    """Abstract base class for data transformation strategies."""
    
    @abstractmethod
    def transform(self, data):
        """Transform the given data according to the strategy."""
        pass

class JSONDataTransformationStrategy(DataTransformationStrategy):
    """Strategy for transforming data into JSON format."""
    
    def transform(self, data):
        """Convert data to JSON."""
        import json
        return json.dumps(data)

class CleanDataTransformationStrategy(DataTransformationStrategy):
    """Strategy for cleaning data (e.g., removing nulls)."""
    
    def transform(self, data):
        """Clean the data by removing null values."""
        return {k: v for k, v in data.items() if v is not None}

# Example usage in data processing facade:
class DataProcessingFacade:
    def __init__(self, transformation_strategy):
        self.transformation_strategy = transformation_strategy
        
    def process_data(self, data):
        return self.transformation_strategy.transform(data)