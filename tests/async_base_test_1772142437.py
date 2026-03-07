# tests/factory.py
from abc import ABC, abstractmethod

class TestFactory(ABC):
    @abstractmethod
    def create_test(self):
        pass

class ModelIntegrationTestFactory(TestFactory):
    def create_test(self):
        from tests.test_model_integration import test_model_integration
        return test_model_integration()

class MinimalTestFactory(TestFactory):
    def create_test(self):
        from tests.minimal_test import minimal_test
        return minimal_test()

# Continue adding factories for other test types

# Usage in async_base_test.py
from factory import TestFactory, ModelIntegrationTestFactory, MinimalTestFactory

def run_tests():
    factories = [
        ModelIntegrationTestFactory(),
        MinimalTestFactory()
        # Add more factories here
    ]
    
    for factory in factories:
        test_case = factory.create_test()
        test_case.run()

if __name__ == '__main__':
    run_tests()