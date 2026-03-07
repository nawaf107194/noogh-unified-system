import pytest
from unified_core.tools_hub import ToolsHub

def test_get_agent_patterns_happy_path():
    """Test normal operation - should return expected patterns dictionary"""
    hub = ToolsHub()
    expected_patterns = {
        "sandboxed_execution": "Code runs in isolated Docker containers",
        "observation_action_loop": "Agent observes → thinks → acts",
        "file_system_awareness": "Agent understands project structure",
        "terminal_integration": "Direct terminal command execution",
        "browser_integration": "Can browse and interact with web pages",
        "multi_agent_delegation": "Tasks can be delegated between agents",
    }
    
    result = hub.get_agent_patterns()
    assert result == expected_patterns
    assert len(result) == 6
    assert "sandboxed_execution" in result
    assert "multi_agent_delegation" in result

def test_get_agent_patterns_edge_cases():
    """Test edge cases including None and invalid inputs"""
    hub = ToolsHub()
    
    # Test with no arguments (normal case)
    result = hub.get_agent_patterns()
    assert isinstance(result, dict)
    
    # Test with None as instance
    with pytest.raises(AttributeError):
        None.get_agent_patterns()
    
    # Test with invalid object
    with pytest.raises(AttributeError):
        object().get_agent_patterns()