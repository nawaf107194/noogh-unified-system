import pytest

from unified_core.orchestration.agent_worker import AgentWorker, AgentRole

class TestAgentWorkerInit:

    def test_happy_path(self):
        worker = AgentWorker()
        assert worker.role == AgentRole.CODE_EXECUTOR
        assert len(worker.handlers) == 2
        assert "ANALYZE_CODE" in worker.handlers
        assert worker.handlers["ANALYZE_CODE"] is worker._analyze_code
        assert "GENERATE_CODE_PATCHES" in worker.handlers
        assert worker.handlers["GENERATE_CODE_PATCHES"] is worker._generate_patches

    def test_edge_case_empty_custom_handlers(self):
        with pytest.raises(ValueError, match="Custom handlers cannot be empty"):
            custom_handlers = {}
            worker = AgentWorker(custom_handlers)

    def test_edge_case_none_custom_handlers(self):
        with pytest.raises(ValueError, match="Custom handlers cannot be None"):
            worker = AgentWorker(None)

    def test_error_case_invalid_role(self):
        with pytest.raises(TypeError, match="Role must be an instance of AgentRole"):
            custom_handlers = {
                "ANALYZE_CODE": self._analyze_code,
                "GENERATE_CODE_PATCHES": self._generate_patches
            }
            worker = AgentWorker("INVALID_ROLE", custom_handlers)

    def test_error_case_invalid_handler(self):
        with pytest.raises(TypeError, match="Handler methods must be callable"):
            custom_handlers = {
                "ANALYZE_CODE": "invalid_handler",
                "GENERATE_CODE_PATCHES": self._generate_patches
            }
            worker = AgentWorker(custom_handlers)