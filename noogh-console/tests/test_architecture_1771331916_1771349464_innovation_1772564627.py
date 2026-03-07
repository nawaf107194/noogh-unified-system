import pytest
from unittest.mock import Mock

class TestClass:
    def test_init_happy_path(self):
        # Create a mock strategy
        mock_strategy = Mock()
        
        # Initialize the class with the mock strategy
        instance = self.ClassUnderTest(mock_strategy)
        
        # Verify that the strategy was set correctly
        assert instance._strategy == mock_strategy

    def test_init_with_none_strategy(self):
        # Initialize the class with None
        instance = self.ClassUnderTest(None)
        
        # Verify that the strategy was set to None
        assert instance._strategy is None