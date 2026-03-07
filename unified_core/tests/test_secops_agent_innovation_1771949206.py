import pytest
from typing import List, Set, Optional
from unified_core.secops_agent import SecOpsAgent, SeverityLevel

# Define some test data and constants
test_max_severity = SeverityLevel.HIGH
blocked_patterns = ["malicious_pattern", "suspicious_function"]
allowed_imports = {"os", "sys"}

def test_happy_path():
    agent = SecOpsAgent(
        max_severity=test_max_severity,
        blocked_patterns=blocked_patterns,
        allowed_imports=allowed_imports
    )
    
    assert agent.max_severity == test_max_severity
    assert agent.blocked_patterns == blocked_patterns
    assert agent.allowed_imports == allowed_imports
    assert agent._audit_count == 0
    assert agent._rejection_count == 0

def test_edge_case_empty_inputs():
    agent = SecOpsAgent()
    
    assert agent.max_severity == SeverityLevel.MEDIUM
    assert agent.blocked_patterns == []
    assert agent.allowed_imports is None
    assert agent._audit_count == 0
    assert agent._rejection_count == 0

def test_edge_case_none_inputs():
    agent = SecOpsAgent(
        max_severity=None,
        blocked_patterns=None,
        allowed_imports=None
    )
    
    assert agent.max_severity == SeverityLevel.MEDIUM
    assert agent.blocked_patterns == []
    assert agent.allowed_imports is None
    assert agent._audit_count == 0
    assert agent._rejection_count == 0

def test_invalid_input_max_severity():
    with pytest.raises(ValueError):
        SecOpsAgent(max_severity="INVALID")

def test_invalid_input_blocked_patterns():
    with pytest.raises(TypeError):
        SecOpsAgent(blocked_patterns={"invalid"})

def test_invalid_input_allowed_imports():
    with pytest.raises(TypeError):
        SecOpsAgent(allowed_imports=["invalid"])