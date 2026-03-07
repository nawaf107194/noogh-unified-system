import pytest

class MockAgent:
    def __init__(self, running):
        self._running = running

def test_is_running_happy_path():
    agent = MockAgent(running=True)
    assert agent.is_running() == True

def test_is_running_false():
    agent = MockAgent(running=False)
    assert agent.is_running() == False

def test_is_running_none():
    agent = MockAgent(running=None)
    assert agent.is_running() is None