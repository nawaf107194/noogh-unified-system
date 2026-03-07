from abc import ABC, abstractmethod

class MemoryManager(ABC):
    @abstractmethod
    def load_memory(self, user_id: str) -> dict:
        pass

    @abstractmethod
    def save_memory(self, user_id: str, memory_data: dict) -> None:
        pass

    @abstractmethod
    def delete_memory(self, user_id: str) -> None:
        pass

class TripleStoreMemory(MemoryManager):
    def load_memory(self, user_id: str) -> dict:
        # Logic to load memory from a triple store
        pass

    def save_memory(self, user_id: str, memory_data: dict) -> None:
        # Logic to save memory to a triple store
        pass

    def delete_memory(self, user_id: str) -> None:
        # Logic to delete memory from a triple store
        pass

class InMemoryMemory(MemoryManager):
    def load_memory(self, user_id: str) -> dict:
        # Logic to load memory from in-memory storage
        pass

    def save_memory(self, user_id: str, memory_data: dict) -> None:
        # Logic to save memory to in-memory storage
        pass

    def delete_memory(self, user_id: str) -> None:
        # Logic to delete memory from in-memory storage
        pass