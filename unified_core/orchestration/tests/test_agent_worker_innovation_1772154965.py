import pytest

from unified_core.orchestration.agent_worker import AgentWorker, AgentRole

class TestAgentWorkerInit:
    def test_happy_path(self):
        # Arrange
        custom_handlers = {
            "ANALYZE_CODE": lambda: None,
            "GENERATE_CODE_PATCHES": lambda: None
        }

        # Act
        agent_worker = AgentWorker(AgentRole.CODE_EXECUTOR, custom_handlers)

        # Assert
        assert isinstance(agent_worker, AgentWorker)
        assert agent_worker.role == AgentRole.CODE_EXECUTOR
        assert agent_worker.handlers == {
            "ANALYZE_CODE": agent_worker._analyze_code,
            "GENERATE_CODE_PATCHES": agent_worker._generate_patches
        }

    def test_edge_case_empty_custom_handlers(self):
        # Arrange
        custom_handlers = {}

        # Act
        agent_worker = AgentWorker(AgentRole.CODE_EXECUTOR, custom_handlers)

        # Assert
        assert isinstance(agent_worker, AgentWorker)
        assert agent_worker.role == AgentRole.CODE_EXECUTOR
        assert agent_worker.handlers == {
            "ANALYZE_CODE": agent_worker._analyze_code,
            "GENERATE_CODE_PATCHES": agent_worker._generate_patches
        }

    def test_edge_case_none_custom_handlers(self):
        # Arrange
        custom_handlers = None

        # Act
        agent_worker = AgentWorker(AgentRole.CODE_EXECUTOR, custom_handlers)

        # Assert
        assert isinstance(agent_worker, AgentWorker)
        assert agent_worker.role == AgentRole.CODE_EXECUTOR
        assert agent_worker.handlers == {
            "ANALYZE_CODE": agent_worker._analyze_code,
            "GENERATE_CODE_PATCHES": agent_worker._generate_patches
        }

    def test_error_case_invalid_role(self):
        # Arrange
        role = object()
        custom_handlers = {
            "ANALYZE_CODE": lambda: None,
            "GENERATE_CODE_PATCHES": lambda: None
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            AgentWorker(role, custom_handlers)

        assert str(exc_info.value) == "Invalid role"