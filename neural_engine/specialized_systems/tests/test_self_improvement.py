import pytest
from typing import Dict, Any

class SelfImprovementSystem:
    def __init__(self, learning_goals):
        self.learning_goals = learning_goals

    def get_improvement_plan(self) -> Dict[str, Any]:
        """Generate a structured plan for system enhancements."""
        return {
            "phase": "Intelligence Expansion",
            "current_targets": [g.topic for g in self.learning_goals],
            "metrics": {
                "knowledge_coverage": 0.82,
                "analytical_precision": 0.94
            }
        }

# Happy path test case
def test_get_improvement_plan_happy_path():
    learning_goals = [
        {"topic": "Artificial Intelligence"},
        {"topic": "Machine Learning"}
    ]
    system = SelfImprovementSystem(learning_goals)
    result = system.get_improvement_plan()
    expected_result = {
        "phase": "Intelligence Expansion",
        "current_targets": ["Artificial Intelligence", "Machine Learning"],
        "metrics": {
            "knowledge_coverage": 0.82,
            "analytical_precision": 0.94
        }
    }
    assert result == expected_result

# Edge case test cases
def test_get_improvement_plan_empty_learning_goals():
    learning_goals = []
    system = SelfImprovementSystem(learning_goals)
    result = system.get_improvement_plan()
    expected_result = {
        "phase": "Intelligence Expansion",
        "current_targets": [],
        "metrics": {
            "knowledge_coverage": 0.82,
            "analytical_precision": 0.94
        }
    }
    assert result == expected_result

def test_get_improvement_plan_none_learning_goals():
    system = SelfImprovementSystem(None)
    result = system.get_improvement_plan()
    expected_result = {
        "phase": "Intelligence Expansion",
        "current_targets": [],
        "metrics": {
            "knowledge_coverage": 0.82,
            "analytical_precision": 0.94
        }
    }
    assert result == expected_result

# Error case test cases
# Note: The provided code does not explicitly raise any errors, so we'll skip this part.