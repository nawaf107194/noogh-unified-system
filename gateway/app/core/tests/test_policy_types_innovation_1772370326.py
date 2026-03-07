import pytest
from dataclasses import asdict
from typing import Dict, Any

# Import the actual class from policy_types.py
from gateway.app.core.policy_types import PolicyType  # Assuming PolicyType is a dataclass and has been defined elsewhere

@pytest.fixture
def sample_policy_type():
    return PolicyType(name="example", value=123)

def test_to_dict_happy_path(sample_policy_type):
    result = sample_policy_type.to_dict()
    assert isinstance(result, dict)
    assert result['name'] == "example"
    assert result['value'] == 123

def test_to_dict_edge_case_empty():
    empty_dict = asdict({})
    result = PolicyType(**empty_dict).to_dict()
    assert isinstance(result, dict)
    assert len(result) == 0

def test_to_dict_edge_case_none():
    with pytest.raises(TypeError):
        PolicyType(None)

def test_to_dict_error_case_invalid_input():
    with pytest.raises(ValueError):
        PolicyType(name="example", value="not an int")