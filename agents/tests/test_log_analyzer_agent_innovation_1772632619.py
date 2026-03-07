import pytest
from unittest.mock import patch, MagicMock
from agents.log_analyzer_agent import LogAnalyzerAgent
from agents.agent import AgentRole

def test_log_analyzer_agent_init_happy_path():
    """Test LogAnalyzerAgent initialization with normal inputs"""
    with patch('agents.log_analyzer_agent.logger') as mock_logger:
        agent = LogAnalyzerAgent()
        
        # Verify custom handlers are set up correctly
        assert len(agent.custom_handlers) == 2
        assert "ANALYZE_LOGS" in agent.custom_handlers
        assert "DETECT_ERROR_PATTERNS" in agent.custom_handlers
        
        # Verify role is set correctly
        assert isinstance(agent.role, AgentRole)
        assert agent.role.name == "log_analyzer"
        
        # Verify logger was called
        mock_logger.info.assert_called_once_with("✅ LogAnalyzerAgent initialized")

def test_log_analyzer_agent_init_edge_case_no_handlers():
    """Test LogAnalyzerAgent initialization with empty custom handlers"""
    with patch('agents.log_analyzer_agent.logger') as mock_logger:
        # Create custom handlers with empty dict
        custom_handlers = {}
        role = AgentRole("log_analyzer")
        
        # Since __init__ is called automatically, we need to mock the super call
        with patch('agents.log_analyzer_agent.Agent.__init__') as mock_super:
            agent = LogAnalyzerAgent()
            
            # Verify super was called with correct arguments
            mock_super.assert_called_once_with(role, custom_handlers)
            
            # Verify logger was called
            mock_logger.info.assert_called_once_with("✅ LogAnalyzerAgent initialized")

def test_log_analyzer_agent_init_edge_case_invalid_role():
    """Test LogAnalyzerAgent initialization with invalid role"""
    with patch('agents.log_analyzer_agent.logger') as mock_logger:
        role = AgentRole("")
        with patch('agents.log_analyzer_agent.Agent.__init__') as mock_super:
            agent = LogAnalyzerAgent()
            
            # Verify super was still called despite invalid role
            mock_super.assert_called_once_with(role, agent.custom_handlers)
            
            # Verify logger was called
            mock_logger.info.assert_called_once_with("✅ LogAnalyzerAgent initialized")