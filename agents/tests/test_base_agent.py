import pytest

from agents.base_agent import BaseAgent

class TestBaseAgentIsRunning:

    def test_happy_path(self):
        agent = BaseAgent()
        agent._running = True
        assert agent.is_running() is True

    def test_edge_case__not_running(self):
        agent = BaseAgent()
        agent._running = False
        assert agent.is_running() is False

    def test_edge_case__none_value(self):
        # Assuming _running is not set, it should return False
        agent = BaseAgent()
        del agent._running  # Remove the attribute to simulate None value
        assert agent.is_running() is False