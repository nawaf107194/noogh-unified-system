import pytest
from unified_core.core.actuators import Actuators
import time
import hashlib

def test_generate_id_happy_path():
    actuators = Actuators()
    op = "test_op"
    result = actuators._generate_id(op)
    assert len(result) == 16, f"Result length should be 16, got {len(result)}"
    assert isinstance(result, str), f"Result should be a string, got {type(result)}"
    expected_prefix = hashlib.sha256(f"{op}:{time.time()}".encode()).hexdigest()[:16]
    assert result.startswith(expected_prefix), f"Result should start with '{expected_prefix}', got '{result}'"

def test_generate_id_edge_case_empty_op():
    actuators = Actuators()
    op = ""
    result = actuators._generate_id(op)
    assert len(result) == 16, f"Result length should be 16 for empty op, got {len(result)}"
    assert isinstance(result, str), f"Result should be a string, got {type(result)}"

def test_generate_id_edge_case_none_op():
    actuators = Actuators()
    op = None
    result = actuators._generate_id(op)
    assert len(result) == 16, f"Result length should be 16 for None op, got {len(result)}"
    assert isinstance(result, str), f"Result should be a string, got {type(result)}"

def test_generate_id_edge_case_boundary_op():
    actuators = Actuators()
    op = "a" * 1024
    result = actuators._generate_id(op)
    assert len(result) == 16, f"Result length should be 16 for long op, got {len(result)}"
    assert isinstance(result, str), f"Result should be a string, got {type(result)}"

def test_generate_id_error_case_invalid_op():
    actuators = Actuators()
    with pytest.raises(ValueError):
        actuators._generate_id(123)