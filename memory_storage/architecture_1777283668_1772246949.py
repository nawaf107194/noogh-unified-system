# memory_storage/architecture_1777283668.py

from collections import namedtuple

class MemoryStorage:
    # Singleton implementation
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MemoryStorage, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.storage = []

    def add_entry(self, entry):
        self.storage.append(entry)

    def get_entries(self):
        return self.storage

# memory_storage/architecture_1777283668.py
from .architecture_1777283668 import MemoryStorage

class MemoryManager:
    # Factory implementation
    def create_memory_storage():
        return MemoryStorage()

# memory_storage/tests/test_architecture_1777283668.py

def test_create_memory_storage():
    manager = MemoryManager()
    storage = manager.create_memory_storage()
    assert isinstance(storage, MemoryStorage)