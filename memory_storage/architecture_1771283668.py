# base_storage.py
class BaseStorage:
    def __init__(self):
        self.data = {}

    def get(self, key):
        """Retrieve an item from storage."""
        return self.data.get(key)

    def set(self, key, value):
        """Store an item in storage."""
        self.data[key] = value

    def delete(self, key):
        """Remove an item from storage if it exists."""
        if key in self.data:
            del self.data[key]

    def clear(self):
        """Clear all items from storage."""
        self.data.clear()

# memory_storage.py
from .base_storage import BaseStorage

class MemoryStorage(BaseStorage):
    def __init__(self):
        super().__init__()

    # Additional methods specific to memory storage can be added here
    def get_all(self):
        return self.data.copy()