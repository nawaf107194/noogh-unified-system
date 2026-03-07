# Create tests/base_test.py

import unittest
from unittest.mock import patch

class BaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up common resources here if needed
        pass
    
    @classmethod
    def tearDownClass(cls):
        # Clean up common resources here if needed
        pass
    
    def setUp(self):
        # Common setup logic for each test method
        pass
    
    def tearDown(self):
        # Common teardown logic for each test method
        pass

# Example usage in other test files:
class TestModelIntegration(BaseTest):
    
    @patch('tests.test_model_integration.some_function')
    def test_some_method(self, mock_function):
        # Test implementation here
        mock_function.assert_called_once()

class TestAsyncBase(BaseTest):
    
    async def test_some_async_method(self):
        # Async test implementation here
        pass