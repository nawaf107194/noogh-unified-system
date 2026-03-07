from dataclasses import asdict, dataclass
from typing import Any, Dict

@dataclass
class PolicyType:
    name: str
    description: str
    enabled: bool

def to_dict(policy_type: PolicyType) -> Dict[str, Any]:
    return asdict(policy_type)

# Test file: test_policy_types.py

import pytest
from gateway.app.core.policy_types import PolicyType, to_dict

@pytest.fixture
def sample_policy_type():
    return PolicyType(name="SamplePolicy", description="This is a sample policy.", enabled=True)

def test_to_dict_happy_path(sample_policy_type):
    result = to_dict(sample_policy_type)
    expected = {
        "name": "SamplePolicy",
        "description": "This is a sample policy.",
        "enabled": True
    }
    assert result == expected

def test_to_dict_edge_case_empty():
    empty_policy_type = PolicyType(name="", description="", enabled=False)
    result = to_dict(empty_policy_type)
    expected = {
        "name": "",
        "description": "",
        "enabled": False
    }
    assert result == expected

def test_to_dict_edge_case_none_values():
    none_policy_type = PolicyType(name=None, description=None, enabled=None)
    result = to_dict(none_policy_type)
    expected = {
        "name": None,
        "description": None,
        "enabled": None
    }
    assert result == expected

def test_to_dict_edge_case_boundary_values():
    boundary_policy_type = PolicyType(name="BoundaryPolicy", description="This is a boundary policy.", enabled=True)
    result = to_dict(boundary_policy_type)
    expected = {
        "name": "BoundaryPolicy",
        "description": "This is a boundary policy.",
        "enabled": True
    }
    assert result == expected

def test_to_dict_error_case_invalid_input():
    with pytest.raises(TypeError):
        to_dict("not a PolicyType instance")