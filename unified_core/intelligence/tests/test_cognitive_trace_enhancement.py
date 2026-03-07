import pytest

from unified_core.intelligence.cognitive_trace_enhancement import CognitiveTraceEnhancement

def test_evaluate_reasoning_happy_path():
    cognitive_trace = CognitiveTraceEnhancement()
    
    thought_history = [
        {'outcome': 'success', 'quality': 5},
        {'outcome': 'failure', 'quality': 3},
        {'outcome': 'success', 'quality': 4}
    ]
    
    expected_average_quality = (5 - 3 + 4) / len(thought_history)
    assert cognitive_trace.evaluate_reasoning(thought_history) == expected_average_quality

def test_evaluate_reasoning_empty_thought_history():
    cognitive_trace = CognitiveTraceEnhancement()
    
    thought_history = []
    
    average_quality = cognitive_trace.evaluate_reasoning(thought_history)
    assert average_quality == 0

def test_evaluate_reasoning_none_input():
    cognitive_trace = CognitiveTraceEnhancement()
    
    with pytest.raises(TypeError):
        cognitive_trace.evaluate_reasoning(None)

def test_evaluate_reasoning_invalid_input_type():
    cognitive_trace = CognitiveTraceEnhancement()
    
    with pytest.raises(TypeError):
        cognitive_trace.evaluate_reasoning("not a list")

def test_evaluate_reasoning_non_dictionary_elements():
    cognitive_trace = CognitiveTraceEnhancement()
    
    thought_history = [
        {'outcome': 'success', 'quality': 5},
        {'outcome': 'failure', 'quality': 3},
        'invalid_element'
    ]
    
    with pytest.raises(ValueError):
        cognitive_trace.evaluate_reasoning(thought_history)

def test_evaluate_reasoning_non_string_outcome():
    cognitive_trace = CognitiveTraceEnhancement()
    
    thought_history = [
        {'outcome': 123, 'quality': 5},  # Non-string outcome
        {'outcome': 'failure', 'quality': 3},
        {'outcome': 'success', 'quality': 4}
    ]
    
    with pytest.raises(ValueError):
        cognitive_trace.evaluate_reasoning(thought_history)

def test_evaluate_reasoning_non_integer_quality():
    cognitive_trace = CognitiveTraceEnhancement()
    
    thought_history = [
        {'outcome': 'success', 'quality': 5},
        {'outcome': 'failure', 'quality': 3},
        {'outcome': 'success', 'quality': '4'}  # Non-integer quality
    ]
    
    with pytest.raises(ValueError):
        cognitive_trace.evaluate_reasoning(thought_history)