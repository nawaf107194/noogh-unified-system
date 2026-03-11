"""
Tests for BaseAgent unified class.
"""
import pytest
import asyncio
from agents.base_agent import BaseAgent


class DummyAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="DummyAgent")
        self.processed = []

    async def start(self):
        self._running = True

    async def stop(self):
        self._running = False

    async def process(self, data):
        self.processed.append(data)


class TestBaseAgent:
    def test_init(self):
        agent = DummyAgent()
        assert agent.name == "DummyAgent"
        assert not agent.is_running()
        assert agent._cycle_count == 0
        assert agent._error_count == 0

    def test_stats(self):
        agent = DummyAgent()
        stats = agent.stats()
        assert stats["name"] == "DummyAgent"
        assert stats["running"] is False
        assert stats["cycles"] == 0

    def test_repr(self):
        agent = DummyAgent()
        r = repr(agent)
        assert "DummyAgent" in r
        assert "running=False" in r

    @pytest.mark.asyncio
    async def test_start_stop(self):
        agent = DummyAgent()
        await agent.start()
        assert agent.is_running()
        await agent.stop()
        assert not agent.is_running()

    @pytest.mark.asyncio
    async def test_process(self):
        agent = DummyAgent()
        await agent.process("test_data")
        assert "test_data" in agent.processed

    def test_uptime_before_start(self):
        agent = DummyAgent()
        assert agent.uptime() == 0.0
