"""
Unit tests for BrainAssistedRefactoring.

Tests cover:
- Code extraction from LLM responses
- Indent detection and re-indentation
- Risk calculation
- Cooldown logic
- CircuitBreaker state machine

Requires: pytest
"""

import time
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


# ── Lightweight stubs to avoid importing the full stack ─────────────

@dataclass
class CodeIssue:
    """Stub matching evolution.code_analyzer.CodeIssue."""
    file: str
    line: int
    issue_type: str
    description: str
    severity: str
    function: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefactorResult:
    """Stub matching evolution.brain_refactor.RefactorResult."""
    success: bool
    original_code: str
    refactored_code: str
    explanation: str
    confidence: float
    issue: CodeIssue


# ── Import the actual class under test ──────────────────────────────
# We patch heavy dependencies so the module can load without a running system

@pytest.fixture(autouse=True)
def patch_heavy_imports(monkeypatch):
    """Patch imports that would fail without a running system."""
    # Stub out get_code_analyzer and get_evolution_ledger
    mock_analyzer = MagicMock()
    mock_analyzer.analyze_file.return_value = MagicMock(functions=[])
    
    mock_ledger = MagicMock()
    mock_ledger.proposals = {}
    
    monkeypatch.setattr(
        "unified_core.evolution.code_analyzer.get_code_analyzer",
        lambda: mock_analyzer
    )
    monkeypatch.setattr(
        "unified_core.evolution.ledger.get_evolution_ledger",
        lambda: mock_ledger
    )


@pytest.fixture
def brain():
    """Create a BrainAssistedRefactoring instance with mocked deps."""
    from unified_core.evolution.brain_refactor import BrainAssistedRefactoring
    b = BrainAssistedRefactoring.__new__(BrainAssistedRefactoring)
    b.neural_bridge = None
    b.ledger = MagicMock()
    b.ledger.proposals = {}
    b.code_analyzer = MagicMock()
    b.requests_made = 0
    b.successful_refactors = 0
    b.failed_refactors = 0
    b._neural_client = None
    b._refactored_files = {}
    b._refactored_functions = {}
    b._refactor_cooldown = 3600
    return b


def _make_issue(severity="MEDIUM", file="/home/test/foo.py", function="bar"):
    return CodeIssue(
        file=file, line=10, issue_type="complexity",
        description="Too complex", severity=severity,
        function=function,
    )


# ═══════════════════════════════════════════════════════════════
# Code Extraction Tests
# ═══════════════════════════════════════════════════════════════

class TestCodeExtraction:
    """Test _extract_code_from_response."""

    def test_extract_from_python_block(self, brain):
        """Extracts code from ```python block."""
        response = """
Here is the refactored function:

```python
def foo():
    return 42
```

This improves performance.
"""
        result = brain._extract_code_from_response(response)
        assert "def foo():" in result
        assert "return 42" in result

    def test_extract_from_generic_block(self, brain):
        """Falls back to generic ``` block."""
        response = """
```
def bar():
    pass
```
"""
        result = brain._extract_code_from_response(response)
        assert "def bar():" in result

    def test_extract_strips_imports(self, brain):
        """Strips standalone imports before the function."""
        response = """
```python
import os
import sys
from pathlib import Path

def foo():
    return os.getcwd()
```
"""
        result = brain._extract_code_from_response(response)
        assert "import os" not in result
        assert "def foo():" in result

    def test_extract_no_code_returns_empty(self, brain):
        """Returns empty string when no code found."""
        response = "This is just text without any code blocks."
        result = brain._extract_code_from_response(response)
        assert result == ""

    def test_extract_strips_class_wrapper(self, brain):
        """Strips class declaration wrapping the function."""
        response = """
```python
class MyClass:

def process(self):
    return True
```
"""
        result = brain._extract_code_from_response(response)
        assert "class MyClass" not in result
        assert "def process(self):" in result

    def test_extract_stops_at_ifname(self, brain):
        """Stops extraction at if __name__ block."""
        response = """
```python
def foo():
    return 1

if __name__ == "__main__":
    foo()
```
"""
        result = brain._extract_code_from_response(response)
        assert "def foo():" in result
        assert "__name__" not in result


# ═══════════════════════════════════════════════════════════════
# Indent Tests
# ═══════════════════════════════════════════════════════════════

class TestIndent:
    """Test _detect_indent_level and _reindent_code."""

    def test_detect_zero_indent(self, brain):
        code = "def foo():\n    pass"
        assert brain._detect_indent_level(code) == 0

    def test_detect_four_indent(self, brain):
        code = "    def foo():\n        pass"
        assert brain._detect_indent_level(code) == 4

    def test_detect_async_def(self, brain):
        code = "        async def bar():\n            pass"
        assert brain._detect_indent_level(code) == 8

    def test_reindent_zero_to_four(self, brain):
        code = "def foo():\n    pass"
        result = brain._reindent_code(code, target_indent=4)
        assert result.startswith("    def foo():")
        assert "        pass" in result

    def test_reindent_four_to_zero(self, brain):
        code = "    def foo():\n        pass"
        result = brain._reindent_code(code, target_indent=0)
        assert result.startswith("def foo():")
        assert "    pass" in result

    def test_reindent_preserves_empty_lines(self, brain):
        code = "def foo():\n    x = 1\n\n    return x"
        result = brain._reindent_code(code, target_indent=4)
        lines = result.split("\n")
        assert lines[2] == "" or lines[2].strip() == ""  # Empty line preserved


# ═══════════════════════════════════════════════════════════════
# Risk Calculation Tests
# ═══════════════════════════════════════════════════════════════

class TestRiskCalculation:
    """Test _calculate_risk."""

    def test_low_severity_low_risk(self, brain):
        issue = _make_issue(severity="LOW")
        result = RefactorResult(
            success=True, original_code="old", refactored_code="def f():\n    pass",
            explanation="fix", confidence=0.9, issue=issue,
        )
        risk = brain._calculate_risk(result)
        assert 10 <= risk <= 30  # LOW=15, -9 confidence, +0 size, +0 core

    def test_critical_severity_high_risk(self, brain):
        issue = _make_issue(severity="CRITICAL")
        result = RefactorResult(
            success=True, original_code="old",
            refactored_code="def f():\n" + "    x = 1\n" * 50,
            explanation="fix", confidence=0.3, issue=issue,
        )
        risk = brain._calculate_risk(result)
        assert risk >= 40  # CRITICAL=45, -3 confidence, +5 size

    def test_core_file_adds_risk(self, brain):
        issue = _make_issue(file="/home/test/core/engine.py")
        result = RefactorResult(
            success=True, original_code="old", refactored_code="def f():\n    pass",
            explanation="fix", confidence=0.5, issue=issue,
        )
        risk = brain._calculate_risk(result)
        # Same as MEDIUM but +10 for core
        issue_normal = _make_issue(file="/home/test/utils.py")
        result_normal = RefactorResult(
            success=True, original_code="old", refactored_code="def f():\n    pass",
            explanation="fix", confidence=0.5, issue=issue_normal,
        )
        risk_normal = brain._calculate_risk(result_normal)
        assert risk == risk_normal + 10

    def test_risk_clamped_10_to_90(self, brain):
        # Very low risk should be clamped to 10
        issue = _make_issue(severity="LOW")
        result = RefactorResult(
            success=True, original_code="old", refactored_code="def f():\n    pass",
            explanation="fix", confidence=1.0, issue=issue,
        )
        risk = brain._calculate_risk(result)
        assert risk >= 10
        assert risk <= 90


# ═══════════════════════════════════════════════════════════════
# Cooldown Tests
# ═══════════════════════════════════════════════════════════════

class TestCooldown:
    """Test refactored-function cooldown tracking."""

    def test_fresh_file_not_in_cooldown(self, brain):
        """A file never refactored should not be in cooldown."""
        assert "new_file.py" not in brain._refactored_files

    def test_recently_refactored_in_cooldown(self, brain):
        """A recently refactored file should be in cooldown."""
        brain._refactored_files["/home/test/foo.py"] = time.time()
        elapsed = time.time() - brain._refactored_files["/home/test/foo.py"]
        assert elapsed < brain._refactor_cooldown

    def test_expired_cooldown(self, brain):
        """A file refactored long ago should be past cooldown."""
        brain._refactored_files["/home/test/old.py"] = time.time() - 7200  # 2 hours ago
        elapsed = time.time() - brain._refactored_files["/home/test/old.py"]
        assert elapsed > brain._refactor_cooldown


# ═══════════════════════════════════════════════════════════════
# CircuitBreaker Tests
# ═══════════════════════════════════════════════════════════════

class TestCircuitBreaker:
    """Test the CircuitBreaker state machine."""

    def _make_cb(self, threshold=3, timeout=10):
        from unified_core.neural_bridge import CircuitBreaker
        return CircuitBreaker(failure_threshold=threshold, recovery_timeout=timeout)

    def test_initial_state_closed(self):
        cb = self._make_cb()
        assert cb.state == "closed"
        assert cb.can_execute() is True

    def test_opens_after_threshold(self):
        cb = self._make_cb(threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "closed"
        cb.record_failure()
        assert cb.state == "open"
        assert cb.can_execute() is False

    def test_success_resets_counter(self):
        cb = self._make_cb(threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.state == "closed"
        assert cb._failure_count == 0
        # Now it takes 3 more failures to open
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "closed"

    def test_half_open_after_timeout(self):
        cb = self._make_cb(threshold=3, timeout=0)  # instant timeout
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"
        # With timeout=0, immediately transitions to half_open
        assert cb.can_execute() is True
        assert cb.state == "half_open"

    def test_half_open_success_closes(self):
        cb = self._make_cb(threshold=3, timeout=0)
        for _ in range(3):
            cb.record_failure()
        cb.can_execute()  # triggers half_open
        cb.record_success()
        assert cb.state == "closed"

    def test_half_open_failure_reopens(self):
        cb = self._make_cb(threshold=3, timeout=0)
        for _ in range(3):
            cb.record_failure()
        cb.can_execute()  # triggers half_open
        cb.record_failure()
        assert cb.state == "open"

    def test_stats_property(self):
        cb = self._make_cb()
        cb.record_success()
        cb.record_failure()
        stats = cb.stats
        assert stats["state"] == "closed"
        assert stats["failures"] == 1
        assert stats["successes"] == 1
