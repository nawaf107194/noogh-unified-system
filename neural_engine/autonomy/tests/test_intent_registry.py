import pytest

class IntentRegistry:
    def __init__(self):
        self.intents = {}

    def register(self, intent):
        """Register an intent."""
        if intent is None or not isinstance(intent, Intent):
            return False
        self.intents[intent.id] = intent
        return True

class Intent:
    def __init__(self, id):
        self.id = id

def test_register_happy_path():
    registry = IntentRegistry()
    intent = Intent(id="test_intent")
    result = registry.register(intent)
    assert result is True
    assert "test_intent" in registry.intents
    assert registry.intents["test_intent"] == intent

def test_register_edge_case_none():
    registry = IntentRegistry()
    result = registry.register(None)
    assert result is False
    assert len(registry.intents) == 0

def test_register_edge_case_invalid_type():
    registry = IntentRegistry()
    result = registry.register("not_an_intent")
    assert result is False
    assert len(registry.intents) == 0