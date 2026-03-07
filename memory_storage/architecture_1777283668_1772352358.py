from abc import ABC, abstractmethod

class MemoryRepository(ABC):
    @abstractmethod
    def get_data(self, key):
        pass

    @abstractmethod
    def save_data(self, key, value):
        pass

    @abstractmethod
    def delete_data(self, key):
        pass

class InMemoryRepository(MemoryRepository):
    def __init__(self):
        self._data = {}

    def get_data(self, key):
        return self._data.get(key)

    def save_data(self, key, value):
        self._data[key] = value

    def delete_data(self, key):
        if key in self._data:
            del self._data[key]

class DatabaseRepository(MemoryRepository):
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def get_data(self, key):
        # Implement database query to retrieve data
        pass

    def save_data(self, key, value):
        # Implement database query to save data
        pass

    def delete_data(self, key):
        # Implement database query to delete data
        pass

# Usage in architecture file
class MemoryStorage:
    def __init__(self, repository: MemoryRepository):
        self.repository = repository

    def get_value(self, key):
        return self.repository.get_data(key)

    def set_value(self, key, value):
        self.repository.save_data(key, value)

    def delete_value(self, key):
        self.repository.delete_data(key)