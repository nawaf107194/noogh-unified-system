import pytest
from unittest.mock import patch, mock_open
import os
import pickle
from functools import wraps

# Import the actual class/function to be tested
from shared.cache_utility import CacheUtility

class TestCacheUtility:
    def setup_method(self):
        self.cache_util = CacheUtility(cache_dir='test_cache')

    def test_happy_path(self):
        # Define a sample function to cache
        @self.cache_util.cache
        def add(a, b):
            return a + b
        
        result1 = add(2, 3)
        assert result1 == 5, "Happy path did not work as expected"
        
        result2 = add(2, 3)  # Should load from cache
        assert result2 == 5, "Cache was not used for subsequent calls"

    @patch('os.path.exists')
    @patch('pickle.load')
    def test_edge_case_cache_exists(self, mock_load, mock_exists):
        mock_exists.return_value = True
        mock_load.return_value = 'cached_result'
        
        # Define a sample function to cache
        @self.cache_util.cache
        def add(a, b):
            return a + b
        
        result = add(2, 3)
        assert result == 'cached_result', "Cached result not used"
    
    @patch('os.path.exists')
    @patch('pickle.load')
    def test_edge_case_cache_not_exists(self, mock_load, mock_exists):
        mock_exists.return_value = False
        mock_load.return_value = 'cached_result'
        
        # Define a sample function to cache
        @self.cache_util.cache
        def add(a, b):
            return a + b
        
        result = add(2, 3)
        assert result == 5, "Function did not execute for non-existent cache"

    @patch('os.path.exists')
    @patch('pickle.dump')
    def test_file_operations(self, mock_dump, mock_exists):
        mock_exists.return_value = False
        
        # Define a sample function to cache
        @self.cache_util.cache
        def add(a, b):
            return a + b
        
        result = add(2, 3)
        assert result == 5, "Function did not execute"
        
        mock_dump.assert_called_once()
    
    @patch('os.path.exists')
    def test_invalid_input(self, mock_exists):
        # Define a sample function with type check
        @self.cache_util.cache
        def add(a, b):
            if not isinstance(a, int) or not isinstance(b, int):
                raise ValueError("Inputs must be integers")
            return a + b
        
        with pytest.raises(ValueError):
            add('2', 3)
        
        with pytest.raises(ValueError):
            add(2, '3')
    
    @patch('os.path.exists')
    def test_async_behavior(self, mock_exists):
        import asyncio

        # Define an async sample function to cache
        @self.cache_util.cache
        async def fetch_data():
            await asyncio.sleep(0.1)
            return "data"
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(fetch_data())
        assert result == "data", "Async function did not execute"

        result_cached = loop.run_until_complete(fetch_data())
        assert result_cached == "data", "Cache was not used for async function"
        
        loop.close()