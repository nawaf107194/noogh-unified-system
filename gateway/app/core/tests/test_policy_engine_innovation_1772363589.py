import pytest

from gateway.app.core.policy_engine import (
    decide,
    CapabilityRequirement,
    RefusalResponse,
    Capability,
)

@pytest.fixture
def test_data():
    return {
        "task": "2 + 2",
        "mode_hint": "auto",
        "session": None,
        "context": {}
    }

def test_decide_math_deterministic_mode(test_data):
    result = decide(**test_data)
    assert result == {
        "__math_result__": True,
        "mode": "MATH_DETERMINISTIC",
        "expression": "2 + 2",
        "result": 4,
        "answer": "4"
    }

def test_decide_hard_security_block(test_data):
    test_data["task"] = "import os"
    result = decide(**test_data)
    assert isinstance(result, RefusalResponse)

def test_decide_planning_mode_explicit(test_data):
    test_data["mode_hint"] = "plan"
    result = decide(**test_data)
    assert isinstance(result, CapabilityRequirement)
    assert result.mode == "PLAN"

def test_decide_execution_mode_explicit(test_data):
    test_data["mode_hint"] = "execute"
    result = decide(**test_data)
    assert isinstance(result, CapabilityRequirement)
    assert result.mode == "EXECUTE"

def test_decide_safe_chat_explicit(test_data):
    test_data["task"] = "Tell me a joke"
    result = decide(**test_data)
    assert isinstance(result, CapabilityRequirement)
    assert result.mode == "EXECUTE"

def test_decide_default_safe_chat(test_data):
    test_data["task"] = "What time is it?"
    result = decide(**test_data)
    assert isinstance(result, CapabilityRequirement)
    assert result.mode == "EXECUTE"

def test_decide_empty_task(test_data):
    test_data["task"] = ""
    result = decide(**test_data)
    assert isinstance(result, CapabilityRequirement)
    assert result.mode == "EXECUTE"

def test_decide_none_task(test_data):
    test_data["task"] = None
    result = decide(**test_data)
    assert isinstance(result, CapabilityRequirement)
    assert result.mode == "EXECUTE"

def test_decide_boundary_case(test_data):
    test_data["task"] = "import sys"
    result = decide(**test_data)
    assert isinstance(result, RefusalResponse)

# Async behavior is not applicable in this synchronous function.