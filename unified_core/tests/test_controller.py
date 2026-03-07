"""
Unit tests for EvolutionController.

Tests cover pure-logic methods that don't require a running system:
- can_auto_execute: risk thresholds per proposal type
- _check_core_interface_lock: file protection
- _find_function_in_file: AST-based function search
- _replace_function_in_file: AST-based function replacement
- _detect_indent / _reindent: indent management

Requires: pytest
"""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

# Use the real types so enum comparisons work
from unified_core.evolution.ledger import (
    EvolutionProposal, ProposalType, ProposalStatus
)


# ── Create controller instance with mocked dependencies ─────────

@pytest.fixture
def ctrl():
    """Create a controller with all heavy deps mocked."""
    # We need to patch all the heavy imports/singletons before importing
    with patch("unified_core.evolution.controller.get_evolution_ledger") as mock_ledger, \
         patch("unified_core.evolution.controller.get_policy_gate") as mock_pg, \
         patch("unified_core.evolution.controller.get_sandbox_executor") as mock_sb, \
         patch("unified_core.evolution.controller.PatchProposer") as mock_pp, \
         patch("unified_core.evolution.controller.GoalAuditEngine") as mock_ga, \
         patch("unified_core.evolution.controller.get_evolution_memory") as mock_em, \
         patch("unified_core.evolution.controller.get_evolution_dreamer") as mock_ed:
        
        mock_ledger.return_value = MagicMock()
        mock_pg.return_value = MagicMock()
        mock_sb.return_value = MagicMock()
        
        from unified_core.evolution.controller import EvolutionController
        c = EvolutionController()
        return c


# ═══════════════════════════════════════════════════════════════
# can_auto_execute Tests
# ═══════════════════════════════════════════════════════════════

class TestCanAutoExecute:
    """Test risk threshold checks per proposal type."""

    def test_config_below_threshold(self, ctrl):
        """Config proposals with low risk should auto-execute."""
        p = EvolutionProposal(
            proposal_id="p1", proposal_type=ProposalType.CONFIG,
            description="test", scope="config", targets=["x.py"],
            diff="d", risk_score=50.0
        )
        assert ctrl.can_auto_execute(p) is True

    def test_config_above_threshold(self, ctrl):
        """Config proposals with high risk should NOT auto-execute."""
        from unified_core.evolution import evolution_config as config
        p = EvolutionProposal(
            proposal_id="p2", proposal_type=ProposalType.CONFIG,
            description="test", scope="config", targets=["x.py"],
            diff="d", risk_score=config.CONFIG_RISK_THRESHOLD + 1
        )
        assert ctrl.can_auto_execute(p) is False

    def test_code_below_threshold(self, ctrl):
        p = EvolutionProposal(
            proposal_id="p3", proposal_type=ProposalType.CODE,
            description="test", scope="code", targets=["x.py"],
            diff="d", risk_score=30.0
        )
        assert ctrl.can_auto_execute(p) is True

    def test_code_above_threshold(self, ctrl):
        from unified_core.evolution import evolution_config as config
        p = EvolutionProposal(
            proposal_id="p4", proposal_type=ProposalType.CODE,
            description="test", scope="code", targets=["x.py"],
            diff="d", risk_score=config.CODE_RISK_THRESHOLD + 1
        )
        assert ctrl.can_auto_execute(p) is False

    def test_disabled_auto_execute(self, ctrl):
        """Disabled auto-execute should reject even low-risk proposals."""
        ctrl.auto_execute_config = False
        p = EvolutionProposal(
            proposal_id="p5", proposal_type=ProposalType.CONFIG,
            description="test", scope="config", targets=["x.py"],
            diff="d", risk_score=10.0
        )
        assert ctrl.can_auto_execute(p) is False


# ═══════════════════════════════════════════════════════════════
# Core Interface Lock Tests
# ═══════════════════════════════════════════════════════════════

class TestCoreInterfaceLock:
    """Test protection of core system files."""

    def test_unlocked_file_passes(self, ctrl):
        p = EvolutionProposal(
            proposal_id="p1", proposal_type=ProposalType.CODE,
            description="test", scope="code", targets=["utils.py"],
            diff="d"
        )
        result = ctrl._check_core_interface_lock(p)
        assert result["pass"] is True

    def test_locked_file_blocked(self, ctrl):
        # Pick the first locked file from the actual config
        from unified_core.evolution.evolution_config import CORE_INTERFACE_LOCKED_FILES
        if not CORE_INTERFACE_LOCKED_FILES:
            pytest.skip("No locked files configured")
        locked_file = list(CORE_INTERFACE_LOCKED_FILES)[0]
        p = EvolutionProposal(
            proposal_id="p2", proposal_type=ProposalType.CODE,
            description="test", scope="code", targets=[f"/path/to/{locked_file}"],
            diff="d"
        )
        result = ctrl._check_core_interface_lock(p)
        assert result["pass"] is False
        assert "CORE_LOCK" in result["reason"]

    def test_no_targets_passes(self, ctrl):
        p = EvolutionProposal(
            proposal_id="p3", proposal_type=ProposalType.CODE,
            description="test", scope="code", targets=[],
            diff="d"
        )
        result = ctrl._check_core_interface_lock(p)
        assert result["pass"] is True

    def test_agent_type_bypasses_lock(self, ctrl):
        from unified_core.evolution.evolution_config import CORE_INTERFACE_LOCKED_FILES
        if not CORE_INTERFACE_LOCKED_FILES:
            pytest.skip("No locked files configured")
        locked_file = list(CORE_INTERFACE_LOCKED_FILES)[0]
        p = EvolutionProposal(
            proposal_id="p4", proposal_type=ProposalType.AGENT,
            description="test", scope="code", targets=[f"/path/to/{locked_file}"],
            diff="d"
        )
        result = ctrl._check_core_interface_lock(p)
        assert result["pass"] is True


# ═══════════════════════════════════════════════════════════════
# AST Function Find/Replace Tests
# ═══════════════════════════════════════════════════════════════

SAMPLE_FILE = '''import os

def hello():
    """Greet."""
    print("hello")

def goodbye():
    """Farewell."""
    print("bye")

class MyClass:
    def method_a(self):
        return 1
    
    def method_b(self):
        return 2
'''


class TestFindFunction:
    """Test AST-based function search."""

    def test_find_top_level(self, ctrl):
        result = ctrl._find_function_in_file(SAMPLE_FILE, "hello")
        assert result is not None
        assert "def hello():" in result
        assert 'print("hello")' in result

    def test_find_second_function(self, ctrl):
        result = ctrl._find_function_in_file(SAMPLE_FILE, "goodbye")
        assert result is not None
        assert "def goodbye():" in result

    def test_find_class_method(self, ctrl):
        result = ctrl._find_function_in_file(SAMPLE_FILE, "method_a")
        assert result is not None
        assert "def method_a(self):" in result

    def test_not_found(self, ctrl):
        result = ctrl._find_function_in_file(SAMPLE_FILE, "nonexistent")
        assert result is None

    def test_syntax_error_returns_none(self, ctrl):
        result = ctrl._find_function_in_file("def broken(:", "broken")
        assert result is None


class TestReplaceFunction:
    """Test AST-based function replacement."""

    def test_replace_top_level(self, ctrl):
        new_code = "def hello():\n    print('REPLACED')"
        result = ctrl._replace_function_in_file(SAMPLE_FILE, "hello", new_code)
        assert result is not None
        assert "REPLACED" in result
        assert "goodbye" in result  # Other functions preserved

    def test_replace_preserves_structure(self, ctrl):
        new_code = "def goodbye():\n    print('NEW')"
        result = ctrl._replace_function_in_file(SAMPLE_FILE, "goodbye", new_code)
        assert "hello" in result
        assert "NEW" in result
        assert "MyClass" in result

    def test_replace_nonexistent_returns_none(self, ctrl):
        result = ctrl._replace_function_in_file(SAMPLE_FILE, "nonexistent", "code")
        assert result is None

    def test_replace_syntax_error_returns_none(self, ctrl):
        result = ctrl._replace_function_in_file("broken{code", "foo", "bar")
        assert result is None


# ═══════════════════════════════════════════════════════════════
# Indent Detection Tests
# ═══════════════════════════════════════════════════════════════

class TestIndentDetection:
    """Test indent detection and reindentation in controller."""

    def test_detect_zero(self, ctrl):
        assert ctrl._detect_indent("def f():\n    pass") == 0

    def test_detect_four(self, ctrl):
        assert ctrl._detect_indent("    def f():\n        pass") == 4

    def test_detect_async(self, ctrl):
        assert ctrl._detect_indent("        async def f():\n            pass") == 8

    def test_reindent_add(self, ctrl):
        code = "def f():\n    pass"
        result = ctrl._reindent(code, 4)
        assert result.startswith("    def f():")

    def test_reindent_remove(self, ctrl):
        code = "    def f():\n        pass"
        result = ctrl._reindent(code, 0)
        assert result.startswith("def f():")
