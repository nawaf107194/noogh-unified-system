# neural_engine/memory_consolidator.py

from abc import ABC, abstractmethod
import time

class MemoryConsolidationStrategy(ABC):
    @abstractmethod
    def consolidate_memory(self, data):
        pass

class LongTermMemoryConsolidation(MemoryConsolidationStrategy):
    def consolidate_memory(self, data):
        # Logic for long-term memory consolidation
        print(f"Consolidating long-term memory... {time.sleep(1)}")
        return f"Long-term memory consolidated: {data}"

class ShortTermMemoryConsolidation(MemoryConsolidationStrategy):
    def consolidate_memory(self, data):
        # Logic for short-term memory consolidation
        print(f"Consolidating short-term memory... {time.sleep(0.5)}")
        return f"Short-term memory consolidated: {data}"

class MemoryConsolidator:
    def __init__(self, strategy: MemoryConsolidationStrategy):
        self.strategy = strategy

    def set_strategy(self, strategy: MemoryConsolidationStrategy):
        self.strategy = strategy

    def consolidate_memory(self, data):
        return self.strategy.consolidate_memory(data)

# Example usage in a module
if __name__ == '__main__':
    long_term_strategy = LongTermMemoryConsolidation()
    short_term_strategy = ShortTermMemoryConsolidation()

    consolidator = MemoryConsolidator(long_term_strategy)
    print(consolidator.consolidate_memory("important_data"))

    consolidator.set_strategy(short_term_strategy)
    print(consolidator.consolidate_memory("temporary_data"))