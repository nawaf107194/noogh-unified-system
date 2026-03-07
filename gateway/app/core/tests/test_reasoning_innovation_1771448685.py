import pytest
from app.core.reasoning import assess_capability, CapabilityAssessment, CapabilityCategory

# Assuming these are defined somewhere in the module
OUT_OF_SCOPE_KEYWORDS = {"admin", "root", "superuser"}
NEURAL_KEYWORDS = {"image", "audio", "video"}

@pytest.fixture
def capability_assessment():
    return assess_capability

def test_happy_path(capability_assessment):
    task = "Send an email to all team members."
    assessment = capability_assessment(task)
    assert assessment.can_handle == True
    assert assessment.category == CapabilityCategory.CAN_DO
    assert assessment.confidence == 0.85
    assert assessment.reason == "Task appears within standard capabilities"

def test_out_of_scope_keyword(capability_assessment):
    task = "Change the admin password."
    assessment = capability_assessment(task)
    assert assessment.can_handle == False
    assert assessment.category == CapabilityCategory.CANNOT_DO
    assert assessment.confidence == 0.95
    assert assessment.reason == f"Request contains security-sensitive keyword: 'admin'"
    assert assessment.suggestion == "Please rephrase without security-sensitive terms"

def test_neural_required_task(capability_assessment):
    task = "Enhance the quality of this image."
    assessment = capability_assessment(task)
    assert assessment.can_handle == True
    assert assessment.category == CapabilityCategory.REQUIRES_NEURAL
    assert assessment.confidence == 0.7
    assert assessment.reason == "Task may require neural services for optimal results"
    assert assessment.suggestion == "Neural services will be used if available"

def test_approval_required_task(capability_assessment):
    task = "Delete all files in the directory."
    assessment = capability_assessment(task)
    assert assessment.can_handle == True
    assert assessment.category == CapabilityCategory.REQUIRES_APPROVAL
    assert assessment.confidence == 0.8
    assert assessment.reason == "Task involves potentially destructive operations"
    assert assessment.requires_approval == True

def test_empty_task(capability_assessment):
    task = ""
    assessment = capability_assessment(task)
    assert assessment.can_handle == True
    assert assessment.category == CapabilityCategory.CAN_DO
    assert assessment.confidence == 0.85
    assert assessment.reason == "Task appears within standard capabilities"

def test_none_task(capability_assessment):
    task = None
    with pytest.raises(TypeError):
        capability_assessment(task)

def test_invalid_input_type(capability_assessment):
    task = 12345
    with pytest.raises(AttributeError):
        capability_assessment(task)

def test_async_behavior_not_applicable(capability_assessment):
    # Since the function does not have async behavior, this test is more about checking the absence of async.
    assert callable(capability_assessment)
    assert not hasattr(capability_assessment, "__await__")
    assert not hasattr(capability_assessment, "__call__")