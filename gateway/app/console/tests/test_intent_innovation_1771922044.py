import pytest

from gateway.app.console.intent import extract_actions

def test_happy_path EXECUTE_mode_with_normal_inputs():
    actions = extract_actions("EXECUTE", "I want to dream for 5 minutes")
    assert actions == [{"action": "dream.start", "args": {"minutes": 5}}]

def test_extract_health_status():
    actions = extract_actions("EXECUTE", "Check my health status")
    assert actions == [{"action": "system.health", "args": {}}]

def test_extract_vision_processing():
    actions = extract_actions("EXECUTE", "Let's process a vision")
    assert actions == [{"action": "vision.process", "args": {}}]

def test_empty_user_text():
    actions = extract_actions("EXECUTE", "")
    assert actions == []

def test_none_user_text():
    actions = extract_actions("EXECUTE", None)
    assert actions == []

def test_mode_not_executable():
    actions = extract_actions("VIEW", "I want to dream for 5 minutes")
    assert actions == []

def test_no_keywords_in_user_text():
    actions = extract_actions("EXECUTE", "Just a regular sentence")
    assert actions == []

def test_boundary_minutes_value():
    actions = extract_actions("EXECUTE", "Dream for 100 minutes")
    assert actions == [{"action": "dream.start", "args": {"minutes": 100}}]

    actions = extract_actions("EXECUTE", "Dream for 0 minutes")
    assert actions == []

def test_non_digit_minutes_value():
    actions = extract_actions("EXECUTE", "Dream for five minutes")
    assert actions == [{"action": "dream.start", "args": {"minutes": 1}}]