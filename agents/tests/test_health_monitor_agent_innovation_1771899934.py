from unittest.mock import Mock, patch
from agents.health_monitor_agent import HealthMonitorAgent

class TestHealthMonitorAgent:

    @patch('agents.health_monitor_agent.AgentRole')
    @patch('logging.info')
    def test_happy_path(self, mock_info, mock_role):
        agent = HealthMonitorAgent()
        assert isinstance(agent.role, AgentRole)
        assert "MONITOR_HEALTH" in agent.custom_handlers
        assert "CHECK_SERVICES" in agent.custom_handlers
        mock_info.assert_called_once_with("✅ HealthMonitorAgent initialized")

    @patch('agents.health_monitor_agent.AgentRole')
    def test_edge_case_empty_custom_handlers(self, mock_role):
        custom_handlers = {}
        agent = HealthMonitorAgent(custom_handlers=custom_handlers)
        assert isinstance(agent.role, AgentRole)
        assert "MONITOR_HEALTH" not in agent.custom_handlers
        assert "CHECK_SERVICES" not in agent.custom_handlers

    @patch('agents.health_monitor_agent.AgentRole')
    def test_edge_case_none_custom_handlers(self, mock_role):
        custom_handlers = None
        agent = HealthMonitorAgent(custom_handlers=custom_handlers)
        assert isinstance(agent.role, AgentRole)
        assert "MONITOR_HEALTH" not in agent.custom_handlers
        assert "CHECK_SERVICES" not in agent.custom_handlers

    @patch('agents.health_monitor_agent.AgentRole')
    def test_error_case_invalid_role(self, mock_role):
        role = "invalid_role"
        with pytest.raises(ValueError) as excinfo:
            HealthMonitorAgent(role=role)
        assert "Invalid role" in str(excinfo.value)

    def test_no_custom_handlers_provided(self):
        agent = HealthMonitorAgent()
        assert "MONITOR_HEALTH" in agent.custom_handlers
        assert "CHECK_SERVICES" in agent.custom_handlers

    @patch('agents.health_monitor_agent.AgentRole')
    def test_async_behavior(self, mock_role):
        agent = HealthMonitorAgent()
        # Assuming _monitor_health and _check_services are async methods for demonstration
        with patch.object(agent, '_monitor_health', new_callable=Mock) as mock_monitor:
            with patch.object(agent, '_check_services', new_callable=Mock) as mock_check:
                agent.run()  # Assuming run method calls these handlers
                mock_monitor.assert_called_once()
                mock_check.assert_called_once()