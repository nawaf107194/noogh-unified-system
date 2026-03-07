import pytest
from neural_engine.meta_intent import summarize, ExpandedIntent

class MockComponent:
    def __init__(self, subsystem):
        self.subsystem = subsystem

def test_summarize_happy_path():
    expanded = ExpandedIntent(
        original_query="test query",
        detected_meta_intent="meta intent",
        components=[MockComponent("subsystem1"), MockComponent("subsystem2")],
        expansion_confidence=0.9,
        estimated_complexity=5,
        warnings=["warning1"],
        commands=["command1", "command2"]
    )
    result = summarize(expanded)
    assert result == {
        "original_query": "test query",
        "meta_intent": "meta intent",
        "subsystems": ["subsystem1", "subsystem2"],
        "tool_count": 2,
        "confidence": 0.9,
        "complexity": 5,
        "warnings": ["warning1"],
        "commands": ["command1", "command2"]
    }

def test_summarize_edge_case_empty_components():
    expanded = ExpandedIntent(
        original_query="test query",
        detected_meta_intent="meta intent",
        components=[],
        expansion_confidence=0.9,
        estimated_complexity=5,
        warnings=["warning1"],
        commands=["command1", "command2"]
    )
    result = summarize(expanded)
    assert result == {
        "original_query": "test query",
        "meta_intent": "meta intent",
        "subsystems": [],
        "tool_count": 0,
        "confidence": 0.9,
        "complexity": 5,
        "warnings": ["warning1"],
        "commands": ["command1", "command2"]
    }

def test_summarize_edge_case_none_expanded():
    result = summarize(None)
    assert result is None

def test_summarize_error_case_invalid_input():
    with pytest.raises(TypeError):
        summarize("not an expanded intent")