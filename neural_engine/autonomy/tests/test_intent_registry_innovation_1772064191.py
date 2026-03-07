import pytest
from typing import List, Pattern
import re
from neural_engine.autonomy.intent_registry import IntentRegistry

class MockIntentRegistry(IntentRegistry):
    def __init__(self, patterns: List[str]):
        super().__init__()
        self.patterns = patterns

def test_post_init_happy_path():
    registry = MockIntentRegistry(["hello", "world"])
    assert all(isinstance(pattern, Pattern) for pattern in registry._compiled_patterns)

def test_post_init_empty_list():
    registry = MockIntentRegistry([])
    assert not registry._compiled_patterns

def test_post_init_none_input():
    registry = MockIntentRegistry(None)
    assert not registry._compiled_patterns

def test_post_init_boundary_case():
    registry = MockIntentRegistry(["a"])
    assert len(registry._compiled_patterns) == 1

def test_post_init_invalid_input():
    with pytest.raises(TypeError):
        MockIntentRegistry([{"invalid": "input"}])