import pytest

from neural_engine.self_learner import SelfLearner

def test_categorize_query_happy_path():
    learner = SelfLearner()
    
    assert learner._categorize_query("What is the status of my system?") == "system"
    assert learner._categorize_query("Write a story for me.") == "creative"
    assert learner._categorize_query("2 + 2") == "math"
    assert learner._categorize_query("Who are you?") == "identity"
    assert learner._categorize_query("Explain the meaning of life.") == "philosophy"
    assert learner._categorize_query("Tell me a joke.") == "general"

def test_categorize_query_edge_cases():
    learner = SelfLearner()
    
    assert learner._categorize_query("") == "general"
    assert learner._categorize_query(None) == "general"
    assert learner._categorize_query("gpu") == "system"
    assert learner._categorize_query("cpu") == "system"

def test_categorize_query_invalid_inputs():
    learner = SelfLearner()
    
    with pytest.raises(TypeError):
        learner._categorize_query(123)
    with pytest.raises(TypeError):
        learner._categorize_query(True)