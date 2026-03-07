import pytest

from neural_engine.orchestrator import Orchestrator

def test_to_dict_happy_path():
    orchestrator = Orchestrator(
        success=True,
        output="expected_output",
        stages_completed=3,
        execution_time=12.5,
        metadata={"key": "value"},
        errors=None
    )
    result = orchestrator.to_dict()
    assert result == {
        "success": True,
        "output": "expected_output",
        "stages_completed": 3,
        "execution_time": 12.5,
        "metadata": {"key": "value"},
        "errors": None
    }

def test_to_dict_empty_values():
    orchestrator = Orchestrator(
        success=False,
        output=None,
        stages_completed=0,
        execution_time=0.0,
        metadata={},
        errors=[]
    )
    result = orchestrator.to_dict()
    assert result == {
        "success": False,
        "output": None,
        "stages_completed": 0,
        "execution_time": 0.0,
        "metadata": {},
        "errors": []
    }

def test_to_dict_with_errors():
    orchestrator = Orchestrator(
        success=False,
        output="error_output",
        stages_completed=2,
        execution_time=3.75,
        metadata={"info": "error"},
        errors=["Error 1", "Error 2"]
    )
    result = orchestrator.to_dict()
    assert result == {
        "success": False,
        "output": "error_output",
        "stages_completed": 2,
        "execution_time": 3.75,
        "metadata": {"info": "error"},
        "errors": ["Error 1", "Error 2"]
    }

def test_to_dict_with_invalid_input():
    orchestrator = Orchestrator(
        success="not_bool",
        output=42,
        stages_completed="not_int",
        execution_time="not_float",
        metadata=["not_dict"],
        errors=1.0
    )
    result = orchestrator.to_dict()
    assert result == {
        "success": None,
        "output": 42,
        "stages_completed": None,
        "execution_time": None,
        "metadata": {},
        "errors": []
    }