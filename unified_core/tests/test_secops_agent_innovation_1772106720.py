import pytest

from unified_core.secops_agent import SecOpsAgent, SeverityLevel

@pytest.fixture
def default_agent():
    return SecOpsAgent()

@pytest.fixture
def custom_agent():
    blocked_patterns = ["pattern1", "pattern2"]
    allowed_imports = {"module1", "module2"}
    max_severity = SeverityLevel.HIGH
    return SecOpsAgent(max_severity, blocked_patterns, allowed_imports)

def test_default_agent(default_agent):
    assert default_agent.max_severity == SeverityLevel.MEDIUM
    assert default_agent.blocked_patterns == []
    assert default_agent.allowed_imports is None
    assert default_agent._audit_count == 0
    assert default_agent._rejection_count == 0

def test_custom_agent(custom_agent):
    assert custom_agent.max_severity == SeverityLevel.HIGH
    assert custom_agent.blocked_patterns == ["pattern1", "pattern2"]
    assert custom_agent.allowed_imports == {"module1", "module2"}
    assert custom_agent._audit_count == 0
    assert custom_agent._rejection_count == 0

def test_empty_severity_level(default_agent):
    with pytest.raises(ValueError) as exc_info:
        SecOpsAgent(max_severity=None)
    assert str(exc_info.value) == "max_severity cannot be None"

def test_invalid_severity_level(default_agent):
    with pytest.raises(ValueError) as exc_info:
        SecOpsAgent(max_severity="invalid")
    assert str(exc_info.value) == "'invalid' is not a valid SeverityLevel"

def test_empty_blocked_patterns(custom_agent):
    assert custom_agent.blocked_patterns == ["pattern1", "pattern2"]

def test_none_blocked_patterns(default_agent):
    with pytest.raises(TypeError) as exc_info:
        SecOpsAgent(blocked_patterns=None)
    assert str(exc_info.value) == "blocked_patterns must be a list or None"

def test_empty_allowed_imports(custom_agent):
    assert custom_agent.allowed_imports == {"module1", "module2"}

def test_none_allowed_imports(default_agent):
    with pytest.raises(TypeError) as exc_info:
        SecOpsAgent(allowed_imports=None)
    assert str(exc_info.value) == "allowed_imports must be a set or None"

def test_async_behavior():
    # Assuming there's no actual async behavior in the __init__ method
    pass  # No-op for now, can add tests if async behavior is introduced later