import pytest
from dataclasses import asdict, dataclass
import json

@dataclass
class TestClass:
    a: int = 1
    b: str = "test"
    c: bool = True

def serialize(obj):
    return json.dumps(asdict(obj))

# Happy path (normal inputs)
def test_serialize_happy_path():
    obj = TestClass(2, "example", False)
    result = serialize(obj)
    assert result == '{"a": 2, "b": "example", "c": false}'

# Edge cases
def test_serialize_empty_obj():
    class EmptyClass:
        pass
    empty_obj = EmptyClass()
    result = serialize(empty_obj)
    assert result == '{}'

def test_serialize_none():
    result = serialize(None)
    assert result is None

def test_serialize_boundary_values():
    obj = TestClass(0, "", False)
    result = serialize(obj)
    assert result == '{"a": 0, "b": "", "c": false}'

# Error cases (if the code explicitly raises them)
# Note: The provided function does not raise any exceptions explicitly.
# If there were specific error conditions in the code, they would be handled here.

# Async behavior (if applicable)
# Note: The provided function is synchronous and does not involve async behavior.