import pytest

class MockWebResearcherAgent:
    def __init__(self, text_parts):
        self._text_parts = text_parts

def test_get_text_happy_path():
    agent = MockWebResearcherAgent(["Line 1", "Line 2"])
    assert agent.get_text() == "Line 1 Line 2"

def test_get_text_empty_input():
    agent = MockWebResearcherAgent([])
    assert agent.get_text() == ""

def test_get_text_none_input():
    agent = MockWebResearcherAgent([None, None])
    assert agent.get_text() == ""

def test_get_text_with_newlines():
    agent = MockWebResearcherAgent(["Line 1\n", "\nLine 2"])
    assert agent.get_text() == "Line 1\n\nLine 2"

def test_get_text_with_spaces():
    agent = MockWebResearcherAgent(["Line 1   ", " Line 2"])
    assert agent.get_text() == "Line 1 Line 2"

def test_get_text_mixed_whitespace():
    agent = MockWebResearcherAgent(["Line 1\n\n", " Line 2   "])
    assert agent.get_text() == "Line 1\n\nLine 2"