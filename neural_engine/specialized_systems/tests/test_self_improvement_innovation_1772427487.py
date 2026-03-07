import pytest

from neural_engine.specialized_systems.self_improvement import SelfImprovementSystem

@pytest.fixture
def system():
    return SelfImprovementSystem()

def test_happy_path(system):
    conversations = [
        "The meeting is scheduled for 2:00 PM.",
        "Please parse the Arabic sentence."
    ]
    expected_gaps = ["advanced_arabic_semantic_parsing", "complex_math_ast_optimization"]
    assert system.identify_knowledge_gaps(conversations) == expected_gaps

def test_edge_case_empty_conversations(system):
    conversations = []
    expected_gaps = ["advanced_arabic_semantic_parsing", "complex_math_ast_optimization"]
    assert system.identify_knowledge_gaps(conversations) == expected_gaps

def test_edge_case_none_conversations(system):
    conversations = None
    expected_gaps = ["advanced_arabic_semantic_parsing", "complex_math_ast_optimization"]
    assert system.identify_knowledge_gaps(conversations) == expected_gaps

def test_error_case_invalid_input_type(system):
    conversations = 12345
    expected_result = []
    assert system.identify_knowledge_gaps(conversations) == expected_result