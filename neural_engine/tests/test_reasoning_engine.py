import pytest
from typing import List, Dict
from neural_engine.reasoning_engine import ReasoningEngine

@pytest.fixture
def reasoning_engine():
    return ReasoningEngine()

def test_prune_history_happy_path(reasoning_engine):
    messages = [
        {"role": "system", "content": "System Prompt"},
        {"role": "user", "content": "User message 1"},
        {"role": "assistant", "content": "Assistant response 1"},
        {"role": "user", "content": "User message 2"},
        {"role": "assistant", "content": "Assistant response 2"},
        {"role": "user", "content": "User message 3"},
        {"role": "assistant", "content": "Assistant response 3"}
    ]
    pruned_messages = reasoning_engine._prune_history(messages)
    assert pruned_messages == [
        {"role": "system", "content": "System Prompt"},
        {"role": "system", "content": "... [سياق مقتطع للتحسين] ..."},
        {"role": "user", "content": "User message 2"},
        {"role": "assistant", "content": "Assistant response 2"},
        {"role": "user", "content": "User message 3"},
        {"role": "assistant", "content": "Assistant response 3"}
    ]

def test_prune_history_empty_list(reasoning_engine):
    messages = []
    pruned_messages = reasoning_engine._prune_history(messages)
    assert pruned_messages == []

def test_prune_history_none_input(reasoning_engine):
    with pytest.raises(TypeError):
        reasoning_engine._prune_history(None)

def test_prune_history_less_than_five_messages(reasoning_engine):
    messages = [
        {"role": "system", "content": "System Prompt"},
        {"role": "user", "content": "User message 1"},
        {"role": "assistant", "content": "Assistant response 1"}
    ]
    pruned_messages = reasoning_engine._prune_history(messages)
    assert pruned_messages == messages

def test_prune_history_invalid_input(reasoning_engine):
    invalid_inputs = [123, "string", {"key": "value"}]
    for invalid_input in invalid_inputs:
        with pytest.raises(TypeError):
            reasoning_engine._prune_history(invalid_input)

# Assuming there is no async behavior in the function as described.
# If there were any async behavior, we would use pytest-asyncio and write tests accordingly.