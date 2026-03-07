import pytest

from neural_engine.reasoning_engine import ReasoningEngine

def test_prune_history_happy_path():
    engine = ReasoningEngine()
    messages = [
        {"role": "system", "content": "System Prompt"},
        {"role": "user", "content": "Message 1"},
        {"role": "assistant", "content": "Response 1"},
        {"role": "user", "content": "Message 2"},
        {"role": "assistant", "content": "Response 2"},
        {"role": "user", "content": "Message 3"},
        {"role": "assistant", "content": "Response 3"}
    ]
    pruned = engine._prune_history(messages)
    assert len(pruned) == 9
    assert pruned[0] == messages[0]
    assert pruned[1]["content"] == "... [سياق مقتطع للتحسين] ..."
    assert pruned[8:] == messages[-4:]

def test_prune_history_edge_empty():
    engine = ReasoningEngine()
    messages = []
    pruned = engine._prune_history(messages)
    assert len(pruned) == 0

def test_prune_history_edge_none():
    engine = ReasoningEngine()
    messages = None
    pruned = engine._prune_history(messages)
    assert pruned is None

def test_prune_history_boundary_five Messages():
    engine = ReasoningEngine()
    messages = [
        {"role": "system", "content": "System Prompt"},
        {"role": "user", "content": "Message 1"},
        {"role": "assistant", "content": "Response 1"}
    ]
    pruned = engine._prune_history(messages)
    assert len(pruned) == 3
    assert pruned[0] == messages[0]
    assert pruned[1:] == messages[1:]

def test_prune_history_invalid_input():
    engine = ReasoningEngine()
    with pytest.raises(TypeError):
        engine._prune_history("Not a list")