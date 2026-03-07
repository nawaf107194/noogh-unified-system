import pytest

from gateway.app.console.intent import extract_actions

def test_extract_actions_happy_path():
    assert extract_actions("EXECUTE", "I want to dream for 5 minutes") == [{"action": "dream.start", "args": {"minutes": 5}}]
    assert extract_actions("EXECUTE", "Check my health status") == [{"action": "system.health", "args": {}}]
    assert extract_actions("EXECUTE", "Process my vision") == [{"action": "vision.process", "args": {}}]

def test_extract_actions_edge_cases():
    assert extract_actions("EXECUTE", "") == []
    assert extract_actions("EXECUTE", None) == []
    assert extract_actions("EXECUTE", "10 minutes of dreams") == [{"action": "dream.start", "args": {"minutes": 10}}]
    assert extract_actions("EXECUTE", "5 hours of dreams") == [{"action": "dream.start", "args": {"minutes": 300}}]

def test_extract_actions_invalid_mode():
    assert extract_actions("INVALID_MODE", "I want to dream for 5 minutes") == []

def test_extract_actions_no_action_words():
    assert extract_actions("EXECUTE", "Just some random text") == []