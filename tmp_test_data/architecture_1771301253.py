from abc import ABC, abstractmethod

class TestDataProvider(ABC):
    @abstractmethod
    def generate(self):
        pass

class SimpleDataGenerator(TestDataProvider):
    def generate(self):
        # Example simple data generation logic
        return {"key": "value"}

class ComplexDataGenerator(TestDataProvider):
    def generate(self):
        # Example complex data generation logic
        return {"complex_key": "complex_value", "nested": {"deep": "data"}}

class TestDataFactory:
    @staticmethod
    def get_data_provider(data_type):
        if data_type == 'simple':
            return SimpleDataGenerator()
        elif data_type == 'complex':
            return ComplexDataGenerator()
        else:
            raise ValueError("Unsupported data type")

# Usage example
if __name__ == "__main__":
    simple_data = TestDataFactory.get_data_provider('simple').generate()
    print(simple_data)
    
    complex_data = TestDataFactory.get_data_provider('complex').generate()
    print(complex_data)