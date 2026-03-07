import pytest

from unified_core.evolution.evolution_memory import EvolutionMemory, Strategy, Outcome

class TestEvolutionMemoryGetStats:

    def test_happy_path(self):
        memory = EvolutionMemory()
        strategy1 = Strategy(id=1, name="Strategy A", accuracy=0.8)
        strategy2 = Strategy(id=2, name="Strategy B", accuracy=0.9)
        outcome1 = Outcome(id=1, success=True, details="Details 1")
        outcome2 = Outcome(id=2, success=False, details="Details 2")

        memory._outcomes.extend([outcome1, outcome2])
        memory._fragile_files.extend(["file1.py", "file2.py"])
        memory.add_strategy(strategy1)
        memory.add_strategy(strategy2)

        expected_stats = {
            "total_outcomes": 2,
            "overall_success_rate": 0.5,
            "fragile_files": 2,
            "strategies": [
                {"id": 2, "name": "Strategy B", "accuracy": 0.9},
                {"id": 1, "name": "Strategy A", "accuracy": 0.8}
            ],
            "recent_outcomes": [
                {"id": 2, "success": False, "details": "Details 2"},
                {"id": 1, "success": True, "details": "Details 1"}
            ]
        }

        assert memory.get_stats() == expected_stats

    def test_empty_memory(self):
        memory = EvolutionMemory()

        expected_stats = {
            "total_outcomes": 0,
            "overall_success_rate": 0.0,
            "fragile_files": 0,
            "strategies": [],
            "recent_outcomes": []
        }

        assert memory.get_stats() == expected_stats

    def test_with_one_strategy(self):
        memory = EvolutionMemory()
        strategy1 = Strategy(id=1, name="Strategy A", accuracy=0.8)
        
        memory.add_strategy(strategy1)

        expected_stats = {
            "total_outcomes": 0,
            "overall_success_rate": None,
            "fragile_files": 0,
            "strategies": [
                {"id": 1, "name": "Strategy A", "accuracy": 0.8}
            ],
            "recent_outcomes": []
        }

        assert memory.get_stats() == expected_stats

    def test_with_one_outcome(self):
        memory = EvolutionMemory()
        outcome1 = Outcome(id=1, success=True, details="Details 1")
        
        memory._outcomes.append(outcome1)

        expected_stats = {
            "total_outcomes": 1,
            "overall_success_rate": 1.0,
            "fragile_files": 0,
            "strategies": [],
            "recent_outcomes": [
                {"id": 1, "success": True, "details": "Details 1"}
            ]
        }

        assert memory.get_stats() == expected_stats

    def test_with_zero_strategies(self):
        memory = EvolutionMemory()

        expected_stats = {
            "total_outcomes": 0,
            "overall_success_rate": None,
            "fragile_files": 0,
            "strategies": [],
            "recent_outcomes": []
        }

        assert memory.get_stats() == expected_stats