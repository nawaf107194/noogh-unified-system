import pytest
from unittest.mock import patch
from agents.log_analyzer_agent import LogAnalyzerAgent
from agents.base_agent import AgentRole

def test_log_analyzer_agent_init_happy_path():
    # Create instance
    agent = LogAnalyzerAgent()
    
    # Verify role is set correctly
    assert agent.role == AgentRole("log_analyzer")
    
    # Verify custom handlers are set
    assert hasattr(agent, 'custom_handlers')
    assert isinstance(agent.custom_handlers, dict)
    assert len(agent.custom_handlers) == 2
    assert "ANALYZE_LOGS" in agent.custom_handlers
    assert "DETECT_ERROR_PATTERNS" in agent.custom_handlers
    
def test_log_analyzer_agent_init_multiple_instances():
    # Create multiple instances
    agent1 = LogAnalyzerAgent()
    agent2 = LogAnalyzerAgent()
    
    # Verify each instance has its own handlers
    assert agent1.custom_handlers != agent2.custom_handlers
    
def test_log_analyzer_agent_init_logging():
    # Mock logger
    with patch('logging.Logger.info') as mock_logger:
        # Create instance
        LogAnalyzerAgent()
        
        # Verify logger called
        mock_logger.assert_called_once_with("✅ LogAnalyzerAgent initialized")
    
def test_log_analyzer_agent_init_no_errors():
    # Test that initialization does not raise exceptions
    try:
        LogAnalyzerAgent()
    except Exception as e:
        pytest.fail(f"Unexpected exception during initialization: {e}")