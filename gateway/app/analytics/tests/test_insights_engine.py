import pytest

from gateway.app.analytics.insights_engine import InsightsEngine, InsightSeverity, Optional

@pytest.fixture
def insights_engine():
    return InsightsEngine

def test_happy_path(insights_engine):
    rule_name = "test_rule"
    severity = InsightSeverity.MEDIUM
    message = "This is a test message."
    explanation = "Explanation for the test message."
    recommendation = "Recommendation to fix the issue."

    engine = insights_engine(rule_name, severity, message, explanation, recommendation)
    
    assert engine.rule_name == rule_name
    assert engine.severity == severity
    assert engine.message == message
    assert engine.explanation == explanation
    assert engine.recommendation == recommendation

def test_edge_case_empty_rule_name(insights_engine):
    severity = InsightSeverity.MEDIUM
    message = "This is a test message."
    explanation = "Explanation for the test message."
    recommendation = "Recommendation to fix the issue."

    with pytest.raises(ValueError) as exc_info:
        insights_engine("", severity, message, explanation, recommendation)
    
    assert str(exc_info.value) == "Rule name cannot be empty"

def test_edge_case_none_rule_name(insights_engine):
    severity = InsightSeverity.MEDIUM
    message = "This is a test message."
    explanation = "Explanation for the test message."
    recommendation = "Recommendation to fix the issue."

    with pytest.raises(ValueError) as exc_info:
        insights_engine(None, severity, message, explanation, recommendation)
    
    assert str(exc_info.value) == "Rule name cannot be None"

def test_edge_case_empty_message(insights_engine):
    rule_name = "test_rule"
    severity = InsightSeverity.MEDIUM
    explanation = "Explanation for the test message."
    recommendation = "Recommendation to fix the issue."

    with pytest.raises(ValueError) as exc_info:
        insights_engine(rule_name, severity, "", explanation, recommendation)
    
    assert str(exc_info.value) == "Message cannot be empty"

def test_edge_case_none_message(insights_engine):
    rule_name = "test_rule"
    severity = InsightSeverity.MEDIUM
    explanation = "Explanation for the test message."
    recommendation = "Recommendation to fix the issue."

    with pytest.raises(ValueError) as exc_info:
        insights_engine(rule_name, severity, None, explanation, recommendation)
    
    assert str(exc_info.value) == "Message cannot be None"

def test_edge_case_empty_explanation(insights_engine):
    rule_name = "test_rule"
    severity = InsightSeverity.MEDIUM
    message = "This is a test message."
    recommendation = "Recommendation to fix the issue."

    with pytest.raises(ValueError) as exc_info:
        insights_engine(rule_name, severity, message, "", recommendation)
    
    assert str(exc_info.value) == "Explanation cannot be empty"

def test_edge_case_none_explanation(insights_engine):
    rule_name = "test_rule"
    severity = InsightSeverity.MEDIUM
    message = "This is a test message."
    recommendation = "Recommendation to fix the issue."

    with pytest.raises(ValueError) as exc_info:
        insights_engine(rule_name, severity, message, None, recommendation)
    
    assert str(exc_info.value) == "Explanation cannot be None"

def test_valid_severity(insights_engine):
    rule_name = "test_rule"
    severity = InsightSeverity.HIGH
    message = "This is a test message."
    explanation = "Explanation for the test message."
    recommendation = "Recommendation to fix the issue."

    engine = insights_engine(rule_name, severity, message, explanation, recommendation)
    
    assert engine.severity == severity

def test_invalid_severity(insights_engine):
    rule_name = "test_rule"
    severity = "INVALID_SEVERITY"
    message = "This is a test message."
    explanation = "Explanation for the test message."
    recommendation = "Recommendation to fix the issue."

    with pytest.raises(ValueError) as exc_info:
        insights_engine(rule_name, severity, message, explanation, recommendation)
    
    assert str(exc_info.value) == "Invalid severity value: INVALID_SEVERITY"