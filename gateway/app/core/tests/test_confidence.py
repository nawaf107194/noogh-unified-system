import pytest
from app.core.confidence import ConfidenceScore, evaluate

def test_happy_path():
    result = evaluate(success=True, iterations=2, has_protocol_violation=False, is_unsupported=False, executed_sandbox=True)
    assert result.value == 1.0
    assert result.level == "HIGH"
    assert len(result.reasons) == 0

def test_no_confidence_without_execution():
    result = evaluate(success=True, iterations=2, has_protocol_violation=False, is_unsupported=False, executed_sandbox=True, mode="PLAN")
    assert result is None

def test_critical_failure_unsupported():
    result = evaluate(success=True, iterations=2, has_protocol_violation=False, is_unsupported=True, executed_sandbox=True)
    assert result.value == 0.0
    assert result.level == "UNSAFE"
    assert result.reasons == ["Task result is UNSUPPORTED or Capability Violation"]

def test_critical_failure_error():
    result = evaluate(success=False, iterations=2, has_protocol_violation=False, is_unsupported=False, executed_sandbox=True, error="Some error")
    assert result.value == 0.0
    assert result.level == "LOW"
    assert result.reasons == ["Task failed: Some error"]

def test_protocol_violation_penalty():
    result = evaluate(success=True, iterations=2, has_protocol_violation=True, is_unsupported=False, executed_sandbox=True)
    assert result.value == 0.6
    assert result.level == "LOW"
    assert result.reasons == ["Protocol violation detected during execution"]

def test_high_iterations_penalty():
    result = evaluate(success=True, iterations=5, has_protocol_violation=False, is_unsupported=False, executed_sandbox=True)
    assert result.value == 0.6
    assert result.level == "MEDIUM"
    assert result.reasons == ["High iteration count (5)"]

def test_sandbox_not_executed():
    result = evaluate(success=True, iterations=2, has_protocol_violation=False, is_unsupported=False, executed_sandbox=False)
    assert result.value == 1.0
    assert result.level == "HIGH"
    assert len(result.reasons) == 0

def test_clamp_value():
    result = evaluate(success=True, iterations=7, has_protocol_violation=False, is_unsupported=False, executed_sandbox=True)
    assert result.value == 0.0
    assert result.level == "LOW"
    assert result.reasons == ["High iteration count (7)"]

def test_invalid_mode():
    with pytest.raises(ValueError):
        evaluate(success=True, iterations=2, has_protocol_violation=False, is_unsupported=False, executed_sandbox=True, mode="INVALID")

def test_invalid_type_iterations():
    with pytest.raises(TypeError):
        evaluate(success=True, iterations="two", has_protocol_violation=False, is_unsupported=False, executed_sandbox=True)

def test_invalid_type_success():
    with pytest.raises(TypeError):
        evaluate(success="True", iterations=2, has_protocol_violation=False, is_unsupported=False, executed_sandbox=True)

def test_invalid_type_has_protocol_violation():
    with pytest.raises(TypeError):
        evaluate(success=True, iterations=2, has_protocol_violation="False", is_unsupported=False, executed_sandbox=True)

def test_invalid_type_is_unsupported():
    with pytest.raises(TypeError):
        evaluate(success=True, iterations=2, has_protocol_violation=False, is_unsupported="False", executed_sandbox=True)

def test_invalid_type_executed_sandbox():
    with pytest.raises(TypeError):
        evaluate(success=True, iterations=2, has_protocol_violation=False, is_unsupported=False, executed_sandbox="True")