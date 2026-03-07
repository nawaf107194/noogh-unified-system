import pytest
from unittest.mock import MagicMock, patch
from ast import Attribute, parse
from typing import Optional

# Mock classes and functions to simulate the environment
class SeverityLevel:
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class VulnerabilityCategory:
    INJECTION = "INJECTION"

class SecurityIssue:
    def __init__(self, category, severity, message, line_number, code_snippet, recommendation):
        self.category = category
        self.severity = severity
        self.message = message
        self.line_number = line_number
        self.code_snippet = code_snippet
        self.recommendation = recommendation

# The function under test
class SecOpsAgent:
    def _check_attribute(self, node: Attribute, code: str) -> Optional[SecurityIssue]:
        dangerous_attrs = {
            "__class__": SeverityLevel.MEDIUM,
            "__bases__": SeverityLevel.HIGH,
            "__subclasses__": SeverityLevel.CRITICAL,
            "__globals__": SeverityLevel.CRITICAL,
            "__code__": SeverityLevel.HIGH,
        }

        if node.attr in dangerous_attrs:
            return SecurityIssue(
                category=VulnerabilityCategory.INJECTION,
                severity=dangerous_attrs[node.attr],
                message=f"Dangerous attribute access: {node.attr}",
                line_number=node.lineno,
                code_snippet=ast.get_source_segment(code, node) or "",
                recommendation="Avoid accessing dunder attributes for security"
            )
        return None

@pytest.fixture
def sec_ops_agent():
    return SecOpsAgent()

# Test cases
def test_happy_path(sec_ops_agent):
    # Create a mock AST node with a dangerous attribute
    node = MagicMock(spec=Attribute)
    node.attr = "__class__"
    node.lineno = 10
    code = "some_code"
    
    result = sec_ops_agent._check_attribute(node, code)
    assert isinstance(result, SecurityIssue)
    assert result.severity == SeverityLevel.MEDIUM
    assert result.message == "Dangerous attribute access: __class__"
    assert result.line_number == 10

def test_edge_case_empty_attribute(sec_ops_agent):
    # Test with an empty attribute name
    node = MagicMock(spec=Attribute)
    node.attr = ""
    node.lineno = 5
    code = "some_code"
    
    result = sec_ops_agent._check_attribute(node, code)
    assert result is None

def test_edge_case_none_attribute(sec_ops_agent):
    # Test with a None attribute name
    node = MagicMock(spec=Attribute)
    node.attr = None
    node.lineno = 7
    code = "some_code"
    
    result = sec_ops_agent._check_attribute(node, code)
    assert result is None

def test_error_case_invalid_attribute(sec_ops_agent):
    # Test with an invalid attribute name
    node = MagicMock(spec=Attribute)
    node.attr = "invalid_attr"
    node.lineno = 8
    code = "some_code"
    
    result = sec_ops_agent._check_attribute(node, code)
    assert result is None

def test_async_behavior_not_applicable(sec_ops_agent):
    # Since the function does not use async/await, this test is not applicable
    pass