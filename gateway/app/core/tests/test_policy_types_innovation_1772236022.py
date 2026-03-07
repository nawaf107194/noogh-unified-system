import pytest
from dataclasses import asdict
from typing import Dict, Any

from gateway.app.core.policy_types import SomePolicyType  # Assuming this is the name of your class

def test_to_dict_happy_path():
    policy = SomePolicyType(field1="value1", field2=42)
    expected_output = {"field1": "value1", "field2": 42}
    assert to_dict(policy) == expected_output

def test_to_dict_edge_case_empty_input():
    class EmptyPolicyType(SomePolicyType):
        pass
    
    policy = EmptyPolicyType()
    expected_output = {}
    assert to_dict(policy) == expected_output

def test_to_dict_edge_case_none_input():
    with pytest.raises(ValueError):
        policy = None
        to_dict(policy)

def test_to_dict_error_case_invalid_input():
    with pytest.raises(TypeError):
        policy = "not a dataclass instance"
        to_dict(policy)