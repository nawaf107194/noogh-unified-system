import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

@pytest.fixture
def evolution_memory():
    from evolution_memory import EvolutionMemory
    return EvolutionMemory()

@pytest.mark.parametrize("trigger_type,expected_strategy", [
    ("test_trigger", "test_strategy"),
    ("", "explore"),
    (None, "explore")
])
def test_get_recommendation_happy_path(evolution_memory, trigger_type, expected_strategy):
    mock_strategy = Mock()
    mock_strategy.name = "test_strategy"
    mock_strategy.success_rate = 0.8
    mock_strategy.total_attempts = 10

    with patch.object(evolution_memory, 'get_best_strategies', return_value=[mock_strategy]):
        result = evolution_memory.get_recommendation(trigger_type)
        
    assert result["strategy"] == expected_strategy
    if expected_strategy == "test_strategy":
        assert result["confidence"] == 0.8
        assert "10 past attempts" in result["basis"]
    else:
        assert result["confidence"] == 0.5
        assert "No history" in result["basis"]

def test_get_recommendation_no_matching_strategies(evolution_memory):
    mock_strategy = Mock()
    mock_strategy.name = "unrelated_strategy"
    
    with patch.object(evolution_memory, 'get_best_strategies', return_value=[mock_strategy]):
        result = evolution_memory.get_recommendation("test_trigger")
    
    assert result["strategy"] == "explore"
    assert result["confidence"] == 0.5
    assert "No history" in result["basis"]

def test_get_recommendation_invalid_input(evolution_memory):
    # Testing with invalid trigger_type (not string)
    result = evolution_memory.get_recommendation(123)
    assert result["strategy"] == "explore"
    assert result["confidence"] == 0.5
    assert "No history" in result["basis"]