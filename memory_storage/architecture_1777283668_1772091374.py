# memory_storage/memory_factory.py

class MemoryStorageFactory:
    def __init__(self):
        self._instances = {}

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = cls(*args, **kwargs)
        return cls._instances[cls]

class MemoryStorage(MemoryStorageFactory):
    def __init__(self):
        super().__init__()
        self.data_store = {}

    def save(self, key, value):
        self.data_store[key] = value

    def load(self, key):
        return self.data_store.get(key)

# Usage
if __name__ == '__main__':
    memory1 = MemoryStorage()
    memory2 = MemoryStorage()

    print("memory1 is memory2:", memory1 is memory2)