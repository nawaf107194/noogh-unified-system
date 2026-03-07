import pytest

from neural_engine.memory_consolidator_1771684842 import MemoryConsolidationStrategy, MemoryConsolidator

class TestMemoryConsolidator:

    @pytest.fixture
    def consolidator(self):
        return MemoryConsolidator()

    def test_set_strategy_happy_path(self, consolidator):
        strategy = MemoryConsolidationStrategy()
        consolidator.set_strategy(strategy)
        assert consolidator.strategy == strategy

    def test_set_strategy_none(self, consolidator):
        consolidator.set_strategy(None)
        assert consolidator.strategy is None

    def test_set_strategy_empty_str(self, consolidator):
        # Assuming MemoryConsolidationStrategy can handle empty string
        strategy = MemoryConsolidationStrategy("")
        consolidator.set_strategy(strategy)
        assert consolidator.strategy == strategy

    def test_set_strategy_invalid_type(self, consolidator):
        with pytest.raises(TypeError) as exc_info:
            consolidator.set_strategy("not a strategy")
        assert str(exc_info.value) == "Invalid memory consolidation strategy type"

# Run the tests using the command:
# pytest /home/noogh/projects/noogh_unified_system/src/neural_engine/memory_consolidator_1771684842.py