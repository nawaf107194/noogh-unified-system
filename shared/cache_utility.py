import os
import pickle
from functools import wraps
from typing import Callable, Any

class CacheUtility:
    def __init__(self, cache_dir: str = 'cache'):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def cache(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = self._generate_cache_key(func.__name__, args, kwargs)
            cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")
            
            if os.path.exists(cache_path):
                with open(cache_path, 'rb') as f:
                    result = pickle.load(f)
                print(f"Loaded from cache: {cache_path}")
                return result
            
            result = func(*args, **kwargs)
            with open(cache_path, 'wb') as f:
                pickle.dump(result, f)
            print(f"Saved to cache: {cache_path}")
            return result
        
        return wrapper
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        arg_str = ''.join(map(str, args))
        kwarg_str = ''.join([f'{k}{v}' for k, v in sorted(kwargs.items())])
        return f"{func_name}_{arg_str}_{kwarg_str}"

if __name__ == "__main__":
    cache_util = CacheUtility()

    @cache_util.cache
    def expensive_function(x, y):
        print("Executing expensive function...")
        return x * y

    print(expensive_function(10, 20))
    print(expensive_function(10, 20))