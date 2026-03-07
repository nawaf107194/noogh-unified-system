import pytest
from typing import Dict, Any

class MockAction:
    def __init__(self, action_id: str, action_type: str, parameters: dict):
        self.action_id = action_id
        self.action_type = action_type
        self.parameters = parameters

class MockOutcome:
    def __init__(self, success: bool, result: Any, error: Exception):
        self.success = success
        self.result = result
        self.error = error

class Consequence:
    def __init__(self, consequence_hash: str, action: MockAction, outcome: MockOutcome, constraints_generated: dict, timestamp: float):
        self.consequence_hash = consequence_hash
        self.action = action
        self.outcome = outcome
        self.constraints_generated = constraints_generated
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "consequence_hash": self.consequence_hash,
            "action_id": self.action.action_id,
            "action_type": self.action.action_type,
            "action_params": self.action.parameters,
            "success": self.outcome.success,
            "result": self.outcome.result,
            "error": self.outcome.error,
            "constraints": self.constraints_generated,
            "timestamp": self.timestamp
        }

@pytest.fixture
def valid_consequence() -> Consequence:
    action = MockAction(action_id="123", action_type="test_action", parameters={"key": "value"})
    outcome = MockOutcome(success=True, result="Success", error=None)
    constraints = {"constraint1": True}
    timestamp = 1672531200.0
    return Consequence(consequence_hash="hash123", action=action, outcome=outcome, constraints_generated=constraints, timestamp=timestamp)

def test_to_dict_happy_path(valid_consequence):
    result = valid_consequence.to_dict()
    assert result == {
        "consequence_hash": "hash123",
        "action_id": "123",
        "action_type": "test_action",
        "action_params": {"key": "value"},
        "success": True,
        "result": "Success",
        "error": None,
        "constraints": {"constraint1": True},
        "timestamp": 1672531200.0
    }

def test_to_dict_empty_values():
    action = MockAction(action_id="", action_type="", parameters={})
    outcome = MockOutcome(success=False, result=None, error=Exception("Test Error"))
    constraints = {}
    timestamp = 0.0
    consequence = Consequence(consequence_hash="", action=action, outcome=outcome, constraints_generated=constraints, timestamp=timestamp)
    result = consequence.to_dict()
    assert result == {
        "consequence_hash": "",
        "action_id": "",
        "action_type": "",
        "action_params": {},
        "success": False,
        "result": None,
        "error": Exception("Test Error"),
        "constraints": {},
        "timestamp": 0.0
    }

def test_to_dict_none_values():
    action = MockAction(action_id=None, action_type=None, parameters=None)
    outcome = MockOutcome(success=None, result=None, error=None)
    constraints = None
    timestamp = None
    consequence = Consequence(consequence_hash=None, action=action, outcome=outcome, constraints_generated=constraints, timestamp=timestamp)
    result = consequence.to_dict()
    assert result == {
        "consequence_hash": None,
        "action_id": None,
        "action_type": None,
        "action_params": None,
        "success": None,
        "result": None,
        "error": None,
        "constraints": None,
        "timestamp": None
    }

def test_to_dict_boundary_values():
    action = MockAction(action_id="123", action_type="test_action", parameters={"key": ""})
    outcome = MockOutcome(success=True, result="", error=Exception())
    constraints = {"constraint1": False}
    timestamp = 0.0
    consequence = Consequence(consequence_hash="hash123", action=action, outcome=outcome, constraints_generated=constraints, timestamp=timestamp)
    result = consequence.to_dict()
    assert result == {
        "consequence_hash": "hash123",
        "action_id": "123",
        "action_type": "test_action",
        "action_params": {"key": ""},
        "success": True,
        "result": "",
        "error": Exception(),
        "constraints": {"constraint1": False},
        "timestamp": 0.0
    }