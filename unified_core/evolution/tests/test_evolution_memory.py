import pytest
from typing import Dict, Any

# Assuming the class is defined as follows for the purpose of this example
class EvolutionMemory:
    def __init__(self, name: str, success_rate: float, total_attempts: int, avg_impact: float):
        self.name = name
        self.success_rate = success_rate
        self.total_attempts = total_attempts
        self.avg_impact = avg_impact

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "success_rate": round(self.success_rate, 3),
            "total_attempts": self.total_attempts,
            "avg_impact": round(self.avg_impact, 3)
        }

@pytest.fixture
def evolution_memory_instance():
    return EvolutionMemory(name="test_evolution", success_rate=0.8567, total_attempts=100, avg_impact=2.3456)

def test_to_dict_happy_path(evolution_memory_instance):
    expected_dict = {
        "name": "test_evolution",
        "success_rate": 0.857,
        "total_attempts": 100,
        "avg_impact": 2.346
    }
    assert evolution_memory_instance.to_dict() == expected_dict

def test_to_dict_empty_name():
    instance = EvolutionMemory(name="", success_rate=0.8567, total_attempts=100, avg_impact=2.3456)
    expected_dict = {
        "name": "",
        "success_rate": 0.857,
        "total_attempts": 100,
        "avg_impact": 2.346
    }
    assert instance.to_dict() == expected_dict

def test_to_dict_none_values():
    instance = EvolutionMemory(name=None, success_rate=None, total_attempts=None, avg_impact=None)
    expected_dict = {
        "name": None,
        "success_rate": 0.000,
        "total_attempts": 0,
        "avg_impact": 0.000
    }
    assert instance.to_dict() == expected_dict

def test_to_dict_boundary_success_rate():
    instance = EvolutionMemory(name="boundary_test", success_rate=0.9995, total_attempts=100, avg_impact=2.3456)
    expected_dict = {
        "name": "boundary_test",
        "success_rate": 1.000,
        "total_attempts": 100,
        "avg_impact": 2.346
    }
    assert instance.to_dict() == expected_dict

def test_to_dict_invalid_inputs():
    with pytest.raises(TypeError):
        EvolutionMemory(name=123, success_rate="not_a_float", total_attempts="not_an_int", avg_impact="not_a_float").to_dict()

def test_to_dict_async_behavior():
    # Since the method does not involve any async operations, this test is not applicable.
    pass