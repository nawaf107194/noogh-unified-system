import pytest
from dataclasses import asdict, dataclass
from typing import Any, Dict

@dataclass
class PolicyType:
    name: str
    description: str

def to_dict(policy_type: PolicyType) -> Dict[str, Any]:
    return asdict(policy_type)

@pytest.mark.parametrize("input_data, expected_output", [
    (PolicyType(name="policy1", description="This is a policy"), {"name": "policy1", "description": "This is a policy"}),
])
def test_to_dict_happy_path(input_data: PolicyType, expected_output: Dict[str, Any]):
    assert to_dict(input_data) == expected_output

@pytest.mark.parametrize("input_data, expected_output", [
    (PolicyType(name="", description=""), {"name": "", "description": ""}),
    (PolicyType(name=None, description=None), {"name": None, "description": None}),
])
def test_to_dict_edge_cases(input_data: PolicyType, expected_output: Dict[str, Any]):
    assert to_dict(input_data) == expected_output

@pytest.mark.parametrize("input_data", [
    123,
    "string",
    [1, 2, 3],
    {"key": "value"},
    None,
])
def test_to_dict_error_cases(input_data):
    result = to_dict(input_data)
    assert result is None