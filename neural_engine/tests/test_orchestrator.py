import pytest
from typing import Dict, Any

# Mock class to represent the object containing the to_dict method
class Orchestrator:
    def __init__(self, success: bool, output: Any, stages_completed: int, execution_time: float, metadata: Dict[str, Any], errors: list):
        self.success = success
        self.output = output
        self.stages_completed = stages_completed
        self.execution_time = execution_time
        self.metadata = metadata
        self.errors = errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "stages_completed": self.stages_completed,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "errors": self.errors,
        }

def test_to_dict_happy_path():
    orchestrator = Orchestrator(
        success=True,
        output="Output data",
        stages_completed=5,
        execution_time=10.5,
        metadata={"key": "value"},
        errors=["Error 1", "Error 2"]
    )
    expected_dict = {
        "success": True,
        "output": "Output data",
        "stages_completed": 5,
        "execution_time": 10.5,
        "metadata": {"key": "value"},
        "errors": ["Error 1", "Error 2"]
    }
    assert orchestrator.to_dict() == expected_dict

def test_to_dict_empty_values():
    orchestrator = Orchestrator(
        success=False,
        output=None,
        stages_completed=0,
        execution_time=0.0,
        metadata={},
        errors=[]
    )
    expected_dict = {
        "success": False,
        "output": None,
        "stages_completed": 0,
        "execution_time": 0.0,
        "metadata": {},
        "errors": []
    }
    assert orchestrator.to_dict() == expected_dict

def test_to_dict_invalid_inputs():
    with pytest.raises(TypeError):
        # Invalid type for 'stages_completed'
        Orchestrator(success=True, output="Output data", stages_completed="five", execution_time=10.5, metadata={"key": "value"}, errors=["Error 1", "Error 2"]).to_dict()
    
    with pytest.raises(TypeError):
        # Invalid type for 'execution_time'
        Orchestrator(success=True, output="Output data", stages_completed=5, execution_time="ten point five", metadata={"key": "value"}, errors=["Error 1", "Error 2"]).to_dict()

def test_to_dict_async_behavior():
    # Since the function is not asynchronous, this test is more about confirming that the function does not block or perform any async operations.
    orchestrator = Orchestrator(
        success=True,
        output="Async output",
        stages_completed=5,
        execution_time=10.5,
        metadata={"key": "async value"},
        errors=["Async error 1", "Async error 2"]
    )
    expected_dict = {
        "success": True,
        "output": "Async output",
        "stages_completed": 5,
        "execution_time": 10.5,
        "metadata": {"key": "async value"},
        "errors": ["Async error 1", "Async error 2"]
    }
    assert orchestrator.to_dict() == expected_dict