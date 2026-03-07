import pytest

from gateway.app.core.reasoning import assess_capability, CapabilityAssessment, CapabilityCategory

# Assuming these are defined somewhere in your codebase
OUT_OF_SCOPE_KEYWORDS = {"password", "secret"}
NEURAL_KEYWORDS = {"image recognition", "speech synthesis"}

@pytest.mark.parametrize(
    "task, expected_output",
    [
        ("Analyze the image for defects", CapabilityAssessment(can_handle=True, category=CapabilityCategory.REQUIRES_NEURAL, confidence=0.7, reason="Task may require neural services for optimal results", suggestion="Neural services will be used if available")),
        ("Delete all files in the directory", CapabilityAssessment(can_handle=True, category=CapabilityCategory.REQUIRES_APPROVAL, confidence=0.8, reason="Task involves potentially destructive operations", requires_approval=True)),
        ("Report on market trends", CapabilityAssessment(can_handle=True, category=CapabilityCategory.CAN_DO, confidence=0.85, reason="Task appears within standard capabilities")),
    ],
)
def test_assess_capability_happy_path(task, expected_output):
    assert assess_capability(task) == expected_output

def test_assess_capability_empty_task():
    result = assess_capability("")
    assert not result.can_handle
    assert result.category == CapabilityCategory.CANNOT_DO
    assert 0.95 <= result.confidence <= 1.0
    assert "empty" in result.reason.lower()

def test_assess_capability_none_task():
    result = assess_capability(None)
    assert not result.can_handle
    assert result.category == CapabilityCategory.CANNOT_DO
    assert 0.95 <= result.confidence <= 1.0
    assert "none" in result.reason.lower()

def test_assess_capability_invalid_input_type():
    with pytest.raises(TypeError):
        assess_capability(123)

def test_assess_capability_out_of_scope_keyword():
    result = assess_capability("Retrieve the password from the database")
    assert not result.can_handle
    assert result.category == CapabilityCategory.CANNOT_DO
    assert 0.95 <= result.confidence <= 1.0
    assert "security-sensitive keyword" in result.reason.lower()

def test_assess_capability_neural_keyword():
    result = assess_capability("Analyze the image for defects")
    assert result.can_handle
    assert result.category == CapabilityCategory.REQUIRES_NEURAL
    assert 0.7 <= result.confidence <= 1.0
    assert "neural services" in result.suggestion.lower()

def test_assess_capability_approval_keyword():
    result = assess_capability("Delete all files in the directory")
    assert result.can_handle
    assert result.category == CapabilityCategory.REQUIRES_APPROVAL
    assert 0.8 <= result.confidence <= 1.0
    assert "potentially destructive operations" in result.reason.lower()