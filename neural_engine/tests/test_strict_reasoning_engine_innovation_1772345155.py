import pytest

from neural_engine.strict_reasoning_engine import StrictReasoningEngine

def test_post_init_happy_path():
    engine = StrictReasoningEngine()
    assert engine.assumptions == []

def test_post_init_no_assumptions():
    engine = StrictReasoningEngine(assumptions=None)
    assert engine.assumptions == []

def test_post_init_with_existing_assumptions():
    assumptions = ["a", "b", "c"]
    engine = StrictReasoningEngine(assumptions=assumptions)
    assert engine.assumptions == assumptions