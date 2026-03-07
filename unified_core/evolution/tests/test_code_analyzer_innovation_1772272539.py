import pytest
from typing import Any, List
from unified_core.evolution.code_analyzer import get_critical_issues

class MockReport:
    def __init__(self, issues: List[dict]):
        self.issues = issues

class CodeIssue:
    def __init__(self, severity: str):
        self.severity = severity

@pytest.fixture
def mock_report():
    return MockReport([
        {"severity": "MEDIUM"},
        {"severity": "HIGH"},
        {"severity": "CRITICAL"},
        {"severity": "LOW"}
    ])

def test_happy_path(mock_report):
    result = get_critical_issues(mock_report)
    expected = [
        CodeIssue("MEDIUM"),
        CodeIssue("HIGH"),
        CodeIssue("CRITICAL")
    ]
    assert result == expected

def test_empty_report():
    report = MockReport([])
    result = get_critical_issues(report)
    assert result == []

def test_none_report():
    result = get_critical_issues(None)
    assert result is None

def test_boundary_severity(mock_report):
    mock_report.issues.append({"severity": "MEDIUM"})
    result = get_critical_issues(mock_report)
    expected = [
        CodeIssue("MEDIUM"),
        CodeIssue("HIGH"),
        CodeIssue("CRITICAL"),
        CodeIssue("MEDIUM")
    ]
    assert result == expected

def test_invalid_severity(mock_report):
    mock_report.issues.append({"severity": "INVALID"})
    result = get_critical_issues(mock_report)
    expected = [
        CodeIssue("MEDIUM"),
        CodeIssue("HIGH"),
        CodeIssue("CRITICAL")
    ]
    assert result == expected