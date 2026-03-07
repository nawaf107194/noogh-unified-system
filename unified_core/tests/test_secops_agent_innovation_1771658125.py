import pytest
from unittest.mock import patch
from unified_core.secops_agent import SecOpsAgent, SecurityIssue, VulnerabilityCategory, SeverityLevel

class TestSecOpsAgent:

    @pytest.fixture
    def agent():
        return SecOpsAgent()

    def test_analyze_ast_happy_path(self, agent):
        code = """
def example_function():
    x = 10 + 20
    return x
"""
        issues = agent._analyze_ast(code)
        assert len(issues) == 0

    def test_analyze_ast_empty_code(self, agent):
        code = ""
        issues = agent._analyze_ast(code)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.category == VulnerabilityCategory.INJECTION
        assert issue.severity == SeverityLevel.HIGH
        assert "Syntax error may indicate code injection" in issue.message

    def test_analyze_ast_none_code(self, agent):
        code = None
        issues = agent._analyze_ast(code)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.category == VulnerabilityCategory.INJECTION
        assert issue.severity == SeverityLevel.HIGH
        assert "Syntax error may indicate code injection" in issue.message

    def test_analyze_ast_syntax_error(self, agent):
        code = "def example_function(): x = 10 + 20"
        issues = agent._analyze_ast(code)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.category == VulnerabilityCategory.INJECTION
        assert issue.severity == SeverityLevel.HIGH
        assert "Syntax error may indicate code injection" in issue.message

    def test_analyze_ast_dangerous_nodes(self, agent):
        class MockNode:
            pass
        agent.DANGEROUS_AST_NODES[MockNode] = "check_method"
        
        with patch.object(agent, "check_method", return_value=SecurityIssue(
            category=VulnerabilityCategory.INJECTION,
            severity=SeverityLevel.HIGH,
            message="Dangerous node detected",
            line_number=1,
            code_snippet="def example_function(): x = 10 + 20",
            recommendation="Fix dangerous node"
        )):
            
            code = """
def example_function():
    x = 10 + 20
"""
            issues = agent._analyze_ast(code)
            assert len(issues) == 1
            issue = issues[0]
            assert issue.category == VulnerabilityCategory.INJECTION
            assert issue.severity == SeverityLevel.HIGH
            assert "Dangerous node detected" in issue.message

    def test_analyze_ast_no_dangerous_nodes(self, agent):
        class MockNode:
            pass
        agent.DANGEROUS_AST_NODES[MockNode] = "check_method"
        
        with patch.object(agent, "check_method", return_value=None):
            
            code = """
def example_function():
    x = 10 + 20
"""
            issues = agent._analyze_ast(code)
            assert len(issues) == 0

    def test_analyze_ast_invalid_input(self, agent):
        with pytest.raises(TypeError):
            agent._analyze_ast(123)

if __name__ == "__main__":
    pytest.main()