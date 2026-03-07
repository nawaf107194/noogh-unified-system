import pytest
from dataclasses import asdict, dataclass
from typing import Any, Dict

@dataclass
class TestClass:
    field1: int
    field2: str

def to_dict(instance):
    return asdict(instance)

def test_to_dict_happy_path():
    instance = TestClass(field1=42, field2="test")
    result = to_dict(instance)
    assert isinstance(result, dict)
    assert result == {'field1': 42, 'field2': 'test'}

def test_to_dict_empty_instance():
    instance = TestClass(field1=0, field2='')
    result = to_dict(instance)
    assert isinstance(result, dict)
    assert result == {'field1': 0, 'field2': ''}

def test_to_dict_none_values():
    instance = TestClass(field1=None, field2=None)
    result = to_dict(instance)
    assert isinstance(result, dict)
    assert result == {'field1': None, 'field2': None}

def test_to_dict_boundary_values():
    instance = TestClass(field1=10**9, field2='a' * 1000)
    result = to_dict(instance)
    assert isinstance(result, dict)
    assert result['field1'] == 10**9
    assert len(result['field2']) == 1000

def test_to_dict_async_behavior():
    # Assuming the function is not async and does not exhibit any async behavior
    pass