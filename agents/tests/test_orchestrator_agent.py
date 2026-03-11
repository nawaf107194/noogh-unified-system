"""
Tests for OrchestratorAgent
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestOrchestratorImport:
    def test_import(self):
        from agents.orchestrator_agent import OrchestratorAgent
        assert OrchestratorAgent is not None

    def test_inherits_base_agent(self):
        from agents.orchestrator_agent import OrchestratorAgent
        from agents.base_agent import BaseAgent
        assert issubclass(OrchestratorAgent, BaseAgent)

    def test_agents_list_not_empty(self):
        from agents.orchestrator_agent import OrchestratorAgent
        assert len(OrchestratorAgent.AGENTS) > 0

    def test_all_entries_have_required_fields(self):
        from agents.orchestrator_agent import OrchestratorAgent
        for entry in OrchestratorAgent.AGENTS:
            assert entry.name
            assert entry.module_path
            assert entry.class_name


class TestOrchestratorStatus:
    def test_status_structure(self):
        from agents.orchestrator_agent import OrchestratorAgent
        orch = OrchestratorAgent()
        status = orch.status()
        assert "uptime" in status
        assert "agents" in status
        assert "total_errors" in status

    def test_initial_error_count_zero(self):
        from agents.orchestrator_agent import OrchestratorAgent
        orch = OrchestratorAgent()
        assert orch._error_count == 0


class TestOrchestratorShutdown:
    def test_stop_sets_shutdown_event(self):
        from agents.orchestrator_agent import OrchestratorAgent

        async def _run():
            orch = OrchestratorAgent()
            await orch.stop()
            assert orch._shutdown_event.is_set()

        asyncio.run(_run())
