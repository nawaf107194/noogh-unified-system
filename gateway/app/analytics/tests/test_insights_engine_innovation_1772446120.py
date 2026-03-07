import pytest

from gateway.app.analytics.insights_engine import InsightsEngine, InsightSeverity
from typing import Optional

@pytest.mark.parametrize("rule_name, severity, message, explanation, recommendation", [
    ("Rule1", InsightSeverity.HIGH, "Message1", "Explanation1", "Recommendation1"),
    ("", InsightSeverity.MEDIUM, "Message2", "Explanation2", None),
    (None, InsightSeverity.LOW, "Message3", "Explanation3", "Recommendation3"),
    ("Rule4", InsightSeverity.CRITICAL, "", "Explanation4", "Recommendation4"),
    ("Rule5", InsightSeverity.WARNING, "Message5", "", "Recommendation5"),
    ("Rule6", InsightSeverity.INFO, "Message6", "Explanation6", ""),
])
def test_init_happy_path(rule_name, severity, message, explanation, recommendation):
    engine = InsightsEngine(rule_name, severity, message, explanation, recommendation)
    assert engine.rule_name == rule_name
    assert engine.severity == severity
    assert engine.message == message
    assert engine.explanation == explanation
    assert engine.recommendation == recommendation

@pytest.mark.parametrize("rule_name, severity, message, explanation, recommendation", [
    (None, None, None, None, None),
])
def test_init_edge_case_none(rule_name, severity, message, explanation, recommendation):
    engine = InsightsEngine(rule_name, severity, message, explanation, recommendation)
    assert engine.rule_name is None
    assert engine.severity is None
    assert engine.message is None
    assert engine.explanation is None
    assert engine.recommendation is None

@pytest.mark.parametrize("rule_name, severity, message, explanation, recommendation", [
    ("", "", "", "", ""),
])
def test_init_edge_case_empty(rule_name, severity, message, explanation, recommendation):
    engine = InsightsEngine(rule_name, severity, message, explanation, recommendation)
    assert engine.rule_name == ""
    assert engine.severity == ""
    assert engine.message == ""
    assert engine.explanation == ""
    assert engine.recommendation == ""

@pytest.mark.parametrize("rule_name, severity, message, explanation, recommendation", [
    (123, "Not a Severity", "Message8", "Explanation8", "Recommendation8"),
])
def test_init_error_case_invalid_input(rule_name, severity, message, explanation, recommendation):
    with pytest.raises(TypeError):
        InsightsEngine(rule_name, severity, message, explanation, recommendation)