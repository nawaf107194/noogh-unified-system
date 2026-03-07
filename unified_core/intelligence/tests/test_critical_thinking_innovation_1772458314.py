import pytest

from unified_core.intelligence.critical_thinking import _question_assumptions

def test_question_assumptions_happy_path():
    assumptions = [
        "The system is stable.",
        "The environment is safe.",
        "The data is accurate."
    ]
    expected_issues = [
        "Unverified assumption: The system is stable.",
        "Unverified assumption: The environment is safe."
    ]
    assert _question_assumptions(assumptions) == expected_issues

def test_question_assumptions_empty_input():
    assumptions = []
    expected_issues = []
    assert _question_assumptions(assumptions) == expected_issues

def test_question_assumptions_none_input():
    assumptions = None
    expected_issues = []
    assert _question_assumptions(assumptions) == expected_issues

def test_question_assumptions_boundary_case():
    assumptions = ["Stable"]
    expected_issues = ["Unverified assumption: Stable"]
    assert _question_assumptions(assumptions) == expected_issues

def test_question_assumptions_no_stable_assumptions():
    assumptions = [
        "The system is dynamic.",
        "The environment is unpredictable."
    ]
    expected_issues = []
    assert _question_assumptions(assumptions) == expected_issues