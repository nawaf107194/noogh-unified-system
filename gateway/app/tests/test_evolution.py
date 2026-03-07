"""
Tests for NOOGH Evolution features.

Tests:
- Reasoning module (Capability Boundaries, Self-Correction, Confidence)
- Extended Tools (Shell, HTTP, Code Analysis)
"""

import pytest

from gateway.app.core.reasoning import (
    CapabilityCategory,
    ConfidenceScorer,
    assess_capability,
    generate_planning_prompt,
    generate_self_correction_prompt,
    parse_self_correction,
)
from gateway.app.core.tools_extended import (
    analyze_code,
    safe_shell_exec,
)


class TestCapabilityBoundaries:
    """Test capability assessment."""

    def test_normal_task_allowed(self):
        """Normal tasks should be allowed."""
        result = assess_capability("Calculate the factorial of 10")
        assert result.can_handle is True
        assert result.category == CapabilityCategory.CAN_DO

    def test_security_keyword_blocked(self):
        """Security-sensitive keywords should be blocked."""
        result = assess_capability("Hack into the system")
        assert result.can_handle is False
        assert "hack" in result.reason.lower()

    def test_neural_task_detected(self):
        """Neural-required tasks should be flagged."""
        result = assess_capability("Analyze this image")
        assert result.can_handle is True
        assert result.category == CapabilityCategory.REQUIRES_NEURAL

    def test_approval_required_detected(self):
        """Destructive tasks should require approval."""
        result = assess_capability("Delete all log files")
        assert result.requires_approval is True


class TestSelfCorrection:
    """Test self-correction protocol."""

    def test_correction_prompt_generated(self):
        """Should generate correction prompt."""
        prompt = generate_self_correction_prompt(error="NameError: name 'x' is not defined", code="print(x)")
        assert "ERROR ANALYSIS" in prompt
        assert "NameError" in prompt
        assert "print(x)" in prompt

    def test_correction_response_parsed(self):
        """Should parse correction response."""
        response = """
ANALYSIS:
The variable x was not defined before use.

ROOT_CAUSE:
Missing variable initialization.

ALTERNATIVE_APPROACH:
Define the variable first.

LESSONS:
Always initialize variables.

CORRECTED_CODE:
```python
x = 10
print(x)
```
"""
        parsed = parse_self_correction(response)
        assert parsed.is_valid is True
        assert "not defined" in parsed.analysis
        assert "x = 10" in parsed.corrected_code


class TestConfidenceScoring:
    """Test confidence scoring."""

    def test_base_confidence(self):
        """Base confidence should be around 0.5."""
        scorer = ConfidenceScorer()
        score = scorer.score("I will try this approach.")
        assert 0.4 <= score.overall <= 0.6

    def test_evidence_increases_confidence(self):
        """Evidence should increase confidence."""
        scorer = ConfidenceScorer()
        score = scorer.score(
            "The code executed successfully because the output shows the correct result.", observation="Result: 42"
        )
        assert score.overall > 0.7

    def test_overconfidence_penalized(self):
        """Overconfidence markers should reduce score."""
        scorer = ConfidenceScorer()
        normal = scorer.score("This approach should work.")
        overconfident = scorer.score("This will definitely absolutely work.")
        assert normal.overall > overconfident.overall


class TestSafeShellExec:
    """Test safe shell executor."""

    def test_allowed_command(self):
        """Allowed commands should execute."""
        result = safe_shell_exec("echo hello")
        assert result.success is True
        assert "hello" in result.output

    def test_blocked_command(self):
        """Non-whitelisted commands should be blocked."""
        result = safe_shell_exec("curl http://example.com")
        assert result.success is False
        assert "not allowed" in result.error.lower()

    def test_dangerous_pattern_blocked(self):
        """Dangerous patterns should be blocked."""
        result = safe_shell_exec("ls; rm -rf /")
        assert result.success is False
        assert "SECURITY" in result.error

    def test_timeout_protection(self):
        """Commands should timeout - tested via sleep command."""
        # Note: sleep is now allowed for testing timeout
        result = safe_shell_exec("sleep 100", timeout=1)
        assert result.success is False
        assert "timeout" in result.error.lower()

    def test_ls_command(self):
        """ls command should work."""
        result = safe_shell_exec("ls -la /tmp")
        assert result.success is True


class TestCodeAnalysis:
    """Test code analysis tool."""

    def test_valid_code_analysis(self):
        """Should analyze valid Python code."""
        code = """
def hello(name):
    return f"Hello, {name}!"

class Greeter:
    def greet(self):
        pass
"""
        result = analyze_code(code)
        assert result.success is True
        assert len(result.functions) == 2  # hello and greet
        assert "Greeter" in result.classes

    def test_syntax_error_detected(self):
        """Should detect syntax errors."""
        code = "def broken("
        result = analyze_code(code)
        assert result.success is False
        assert "syntax" in result.error.lower()

    def test_issues_detected(self):
        """Should detect potential issues."""
        code = """
while True:
    pass
"""
        result = analyze_code(code)
        assert len(result.issues) > 0
        assert any("infinite" in i.lower() for i in result.issues)

    def test_imports_extracted(self):
        """Should extract imports."""
        code = """
import os
from pathlib import Path
"""
        result = analyze_code(code)
        assert "os" in result.imports


class TestPlanningMode:
    """Test planning mode prompt."""

    def test_planning_prompt_generated(self):
        """Should generate planning prompt."""
        prompt = generate_planning_prompt("Create a web scraper")
        assert "PLANNING MODE" in prompt
        assert "DO NOT EXECUTE" in prompt
        assert "Create a web scraper" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
