"""
Test ReAct Loop Budget Protection Against Override Bypass
High-severity security test: Ensure absolute maximums cannot be bypassed.
"""
import pytest
from unittest.mock import Mock


def test_react_bridge_enforces_absolute_max_iterations():
    """
    HIGH SECURITY TEST:
    Verify that ReActBridge cannot bypass MAX_ITERATIONS absolute limit.
    
    Even if gateway config sets max_iterations=999, the system must
    cap it to the absolute maximum (10).
    """
    from gateway.app.core.react_bridge import ReActBridge, ReActConfig
    
    # Try to set excessive iterations
    malicious_config = ReActConfig(
        max_iterations=999,  # Attempt bypass
        tool_budget_per_cycle=2
    )
    
    mock_parser = Mock()
    mock_memory = Mock()
    
    bridge = ReActBridge(mock_parser, mock_memory, malicious_config)
    
    # Trigger init of constrained loop
    loop = bridge._get_or_create_loop()
    
    # Verify it was capped to absolute maximum
    ABSOLUTE_MAX = 10
    assert loop.MAX_ITERATIONS <= ABSOLUTE_MAX, \
        f"MAX_ITERATIONS bypass detected: {loop.MAX_ITERATIONS} > {ABSOLUTE_MAX}"
    
    # Should be capped to 10, not 999
    assert loop.MAX_ITERATIONS == ABSOLUTE_MAX


def test_react_bridge_enforces_absolute_max_tool_budget():
    """
    HIGH SECURITY TEST:
    Verify that tool budget cannot be bypassed.
    """
    from gateway.app.core.react_bridge import ReActBridge, ReActConfig
    
    # Try to set excessive tool budget
    malicious_config = ReActConfig(
        max_iterations=5,
        tool_budget_per_cycle=100  # Attempt bypass
    )
    
    mock_parser = Mock()
    mock_memory = Mock()
    
    bridge = ReActBridge(mock_parser, mock_memory, malicious_config)
    loop = bridge._get_or_create_loop()
    
    # Verify capped to absolute maximum
    ABSOLUTE_MAX_BUDGET = 5
    assert loop.TOOL_BUDGET_PER_CYCLE <= ABSOLUTE_MAX_BUDGET, \
        f"Tool budget bypass detected: {loop.TOOL_BUDGET_PER_CYCLE} > {ABSOLUTE_MAX_BUDGET}"
    
    assert loop.TOOL_BUDGET_PER_CYCLE == ABSOLUTE_MAX_BUDGET


def test_react_bridge_allows_safe_config():
    """
    Verify that reasonable configs are accepted.
    """
    from gateway.app.core.react_bridge import ReActBridge, ReActConfig
    
    # Safe config within limits
    safe_config = ReActConfig(
        max_iterations=5,
        tool_budget_per_cycle=3
    )
    
    mock_parser = Mock()
    mock_memory = Mock()
    
    bridge = ReActBridge(mock_parser, mock_memory, safe_config)
    loop = bridge._get_or_create_loop()
    
    # Should match requested values (within limits)
    assert loop.MAX_ITERATIONS == 5
    assert loop.TOOL_BUDGET_PER_CYCLE == 3


def test_constrained_loop_default_limits_are_safe():
    """
    Verify ConstrainedReActLoop has safe defaults.
    """
    from neural_engine.reasoning.react_loop import ConstrainedReActLoop
    from unittest.mock import Mock
    
    loop = ConstrainedReActLoop(
        reasoning_engine=Mock(),
        tool_executor=Mock()
    )
    
    # Defaults should be conservative
    assert loop.MAX_ITERATIONS <= 10, f"Default MAX_ITERATIONS too high: {loop.MAX_ITERATIONS}"
    assert loop.TOOL_BUDGET_PER_CYCLE <= 5, f"Default TOOL_BUDGET too high: {loop.TOOL_BUDGET_PER_CYCLE}"
    assert loop.OBSERVATION_MAX_CHARS <= 5000, f"Default OBSERVATION_MAX too high: {loop.OBSERVATION_MAX_CHARS}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
