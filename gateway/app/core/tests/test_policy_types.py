import pytest
from dataclasses import asdict, dataclass
from typing import Any, Dict

@dataclass
class PolicyType:
    name: str
    description: str
    active: bool

def to_dict(self) -> Dict[str, Any]:
    return asdict(self)

@pytest.fixture
def policy_type():
    return PolicyType(name="example", description="This is an example policy", active=True)

def test_to_dict_happy_path(policy_type):
    result = to_dict(policy_type)
    assert result == {
        "name": "example",
        "description": "This is an example policy",
        "active": True
    }

def test_to_dict_empty_input():
    empty_policy_type = PolicyType(name="", description="", active=False)
    result = to_dict(empty_policy_type)
    assert result == {
        "name": "",
        "description": "",
        "active": False
    }

def test_to_dict_none_input():
    none_policy_type = PolicyType(name=None, description=None, active=None)
    result = to_dict(none_policy_type)
    assert result == {
        "name": None,
        "description": None,
        "active": None
    }

def test_to_dict_boundary_values():
    boundary_policy_type = PolicyType(name="a" * 100, description="b" * 256, active=True)
    result = to_dict(boundary_policy_type)
    assert result == {
        "name": "a" * 100,
        "description": "b" * 256,
        "active": True
    }

def test_to_dict_invalid_inputs():
    invalid_policy_type = PolicyType(name=123, description=45.67, active="invalid")
    result = to_dict(invalid_policy_type)
    assert result == {
        "name": 123,
        "description": 45.67,
        "active": "invalid"
    }