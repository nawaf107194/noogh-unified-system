import pytest
from unittest.mock import patch, MagicMock
from gateway.app.core.policy_engine import PolicyEngine, CapabilityRequirement, RefusalResponse
from gateway.app.core.capabilities import Capability

# Mocking the math evaluator
def mock_is_math_query(query):
    return query.startswith('math ')

def mock_process_math_query(query):
    if query.startswith('math '):
        return {
            "success": True,
            "expression": query,
            "result": 42,
            "answer_ar": "The answer is 42"
        }
    return None

# Test setup
@pytest.fixture
def policy_engine():
    return PolicyEngine()

# Happy path tests
def test_math_query(policy_engine):
    with patch('gateway.app.core.policy_engine.is_math_query', mock_is_math_query), \
         patch('gateway.app.core.policy_engine.process_math_query', mock_process_math_query):
        result = policy_engine.decide('math calculate 6*7')
        assert result["__math_result__"] == True
        assert result["mode"] == "MATH_DETERMINISTIC"
        assert result["expression"] == "math calculate 6*7"
        assert result["result"] == 42
        assert result["answer"] == "The answer is 42"

def test_hard_security_block(policy_engine):
    with patch.object(PolicyEngine, 'FORBIDDEN_PATTERNS', {'sensitive': [r'sensitive']}):
        result = policy_engine.decide('access sensitive data')
        assert isinstance(result, RefusalResponse)
        assert result.code == "CapabilityBoundaryViolation"
        assert result.message == "Request requires forbidden capability: SENSITIVE"
        assert result.allowed_alternatives == [
            "Work with local files only",
            "Ask for a plan or explanation",
            "Use Python for local computation",
        ]

def test_planning_mode_explicit(policy_engine):
    result = policy_engine.decide('create a project plan', mode_hint='plan')
    assert isinstance(result, CapabilityRequirement)
    assert result.required == {Capability.PROJECT_PLAN}
    assert result.forbidden == {Capability.CODE_EXEC, Capability.FS_WRITE}
    assert result.mode == "PLAN"
    assert result.reason == "Explicit plan mode requested."

def test_execution_mode_explicit(policy_engine):
    result = policy_engine.decide('run a script', mode_hint='execute')
    assert isinstance(result, CapabilityRequirement)
    assert result.required == {Capability.CODE_EXEC, Capability.FS_READ}
    assert result.forbidden == {Capability.INTERNET, Capability.SHELL}
    assert result.mode == "EXECUTE"
    assert result.reason == "Explicit execute mode requested."

def test_safe_chat_mode(policy_engine):
    with patch.object(PolicyEngine, 'SAFE_PATTERNS', [r'hello']):
        result = policy_engine.decide('hello')
        assert isinstance(result, CapabilityRequirement)
        assert result.required == set()
        assert result.forbidden == {Capability.INTERNET, Capability.SHELL}
        assert result.mode == "EXECUTE"
        assert result.reason == "Safe conversational / compute / read-only request."

# Edge case tests
def test_empty_task(policy_engine):
    result = policy_engine.decide('')
    assert isinstance(result, CapabilityRequirement)
    assert result.required == set()
    assert result.forbidden == {Capability.INTERNET, Capability.SHELL}
    assert result.mode == "EXECUTE"
    assert result.reason == "Implicit safe chat intent."

def test_none_task(policy_engine):
    result = policy_engine.decide(None)
    assert isinstance(result, CapabilityRequirement)
    assert result.required == set()
    assert result.forbidden == {Capability.INTERNET, Capability.SHELL}
    assert result.mode == "EXECUTE"
    assert result.reason == "Implicit safe chat intent."

# Error case tests
def test_invalid_mode_hint(policy_engine):
    with pytest.raises(ValueError) as excinfo:
        policy_engine.decide('do something', mode_hint='invalid')
    assert "Invalid mode hint provided" in str(excinfo.value)

# Async behavior tests (assuming async version exists)
@pytest.mark.asyncio
async def test_async_decide(policy_engine):
    with patch.object(PolicyEngine, 'decide', new=MagicMock(return_value=CapabilityRequirement(required={Capability.PROJECT_PLAN}, forbidden={Capability.CODE_EXEC, Capability.FS_WRITE}, mode="PLAN", reason="Async planning intent."))):
        result = await policy_engine.async_decide('create a project plan', mode_hint='plan')
        assert isinstance(result, CapabilityRequirement)
        assert result.required == {Capability.PROJECT_PLAN}
        assert result.forbidden == {Capability.CODE_EXEC, Capability.FS_WRITE}
        assert result.mode == "PLAN"
        assert result.reason == "Async planning intent."