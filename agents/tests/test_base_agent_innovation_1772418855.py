import pytest

from agents.base_agent import BaseAgent

class TestBaseAgentInit:

    def test_happy_path(self):
        agent = BaseAgent()
        assert not agent._running

    def test_edge_case_none(self):
        with pytest.raises(TypeError):
            agent = BaseAgent(None)

    def test_edge_case_empty_string(self):
        with pytest.raises(TypeError):
            agent = BaseAgent("")

    def test_edge_case_number(self):
        with pytest.raises(TypeError):
            agent = BaseAgent(123)