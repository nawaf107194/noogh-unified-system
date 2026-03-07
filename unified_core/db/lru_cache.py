# unified_core/db/lru_cache.py

from functools import lru_cache
from typing import Any, Callable

class LRUCache:
    def __init__(self, maxsize: int):
        self.maxsize = maxsize
        self.cache = {}

    def __call__(self, func: Callable) -> Callable:
        @lru_cache(maxsize=self.maxsize)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

# Example usage
class MemoryStore:
    def __init__(self):
        self.data = {}
    
    @LRUCache(maxsize=128)  # Cache up to 128 most recent calls
    def get_data(self, key: str) -> Any:
        return self.data.get(key)

# Usage
if __name__ == '__main__':
    store = MemoryStore()
    store.data['key1'] = 'value1'
    
    print(store.get_data('key1'))  # This will be cached
    print(store.get_data('key2'))  # This will not be cached, as 'key2' is not in the cache yet