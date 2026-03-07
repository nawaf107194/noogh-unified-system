import pytest
from typing import Dict, Any

class MockEvaluation:
    def __init__(self, issues=None):
        self.issues = issues or []

def test_happy_path():
    response = {"final_answer": "42"}
    evaluation = MockEvaluation(issues=[])
    result = _final_safety_check(response, evaluation)
    assert result == {"safe": True, "reason": None}

def test_no_critical_issues():
    response = {"final_answer": "42"}
    evaluation = MockEvaluation(issues=["OTHER_ISSUE"])
    result = _final_safety_check(response, evaluation)
    assert result == {"safe": True, "reason": None}

def test_response_is_n_a():
    response = {"final_answer": "N/A"}
    evaluation = MockEvaluation(issues=[])
    result = _final_safety_check(response, evaluation)
    assert result == {"safe": False, "reason": "Response is N/A"}

def test_critical_issue_present():
    critical_issues = ["DIMENSIONAL_INCONSISTENCY", "FORMULA_MEMORIZATION", "UNVERIFIED_STEPS"]
    for issue in critical_issues:
        response = {"final_answer": "42"}
        evaluation = MockEvaluation(issues=[issue])
        result = _final_safety_check(response, evaluation)
        assert result == {"safe": False, "reason": f"Critical issue present: {issue}"}

def test_empty_evaluation():
    response = {"final_answer": "42"}
    evaluation = MockEvaluation([])
    result = _final_safety_check(response, evaluation)
    assert result == {"safe": True, "reason": None}

def test_none_evaluation():
    response = {"final_answer": "42"}
    evaluation = None
    result = _final_safety_check(response, evaluation)
    assert result == {"safe": False, "reason": "Evaluation is None"}

def test_invalid_response():
    response = None
    evaluation = MockEvaluation(issues=[])
    result = _final_safety_check(response, evaluation)
    assert result == {"safe": False, "reason": "Response is None"}