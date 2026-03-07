import pytest
from noogh_unified_system.src.agents.dependency_auditor_agent import DependencyAuditorAgent, AgentRole
from noogh_unified_system.src.utils.logger import logger

@pytest.fixture
def auditor_agent():
    return DependencyAuditorAgent()

class TestDependencyAuditorAgent:
    def test_happy_path(self, auditor_agent):
        assert isinstance(auditor_agent.role, AgentRole)
        assert auditor_agent.role.name == "dependency_auditor"
        assert hasattr(auditor_agent, "_audit_dependencies")
        assert hasattr(auditor_agent, "_check_vulnerabilities")

    def test_custom_handlers_registered(self, auditor_agent):
        custom_handlers = {
            "AUDIT_DEPS": auditor_agent._audit_dependencies,
            "CHECK_VULNERABILITIES": auditor_agent._check_vulnerabilities,
        }
        for key, handler in custom_handlers.items():
            assert callable(handler)
            assert hasattr(auditor_agent, f"handle_{key}")

    def test_logger_info(self, caplog):
        with caplog.at_level(logger.info.level):
            agent = DependencyAuditorAgent()
        assert "✅ DependencyAuditorAgent initialized" in caplog.text