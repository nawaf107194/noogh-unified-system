import pytest
from typing import Dict, Any

class AdvancedReasoning:
    def __init__(self, pattern_type: str, description: str, confidence: float, occurrences: int, examples: list, metadata: dict):
        self.pattern_type = pattern_type
        self.description = description
        self.confidence = confidence
        self.occurrences = occurrences
        self.examples = examples
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "description": self.description,
            "confidence": self.confidence,
            "occurrences": self.occurrences,
            "examples": self.examples,
            "metadata": self.metadata,
        }

@pytest.fixture
def example_instance():
    return AdvancedReasoning(
        pattern_type="example_type",
        description="example_description",
        confidence=0.95,
        occurrences=3,
        examples=["example1", "example2"],
        metadata={"key": "value"}
    )

def test_to_dict_happy_path(example_instance):
    expected_output = {
        "pattern_type": "example_type",
        "description": "example_description",
        "confidence": 0.95,
        "occurrences": 3,
        "examples": ["example1", "example2"],
        "metadata": {"key": "value"}
    }
    assert example_instance.to_dict() == expected_output

def test_to_dict_edge_case_empty_values():
    instance = AdvancedReasoning(
        pattern_type="",
        description="",
        confidence=0.0,
        occurrences=0,
        examples=[],
        metadata={}
    )
    expected_output = {
        "pattern_type": "",
        "description": "",
        "confidence": 0.0,
        "occurrences": 0,
        "examples": [],
        "metadata": {}
    }
    assert instance.to_dict() == expected_output

def test_to_dict_edge_case_none_values():
    instance = AdvancedReasoning(
        pattern_type=None,
        description=None,
        confidence=None,
        occurrences=None,
        examples=None,
        metadata=None
    )
    expected_output = {
        "pattern_type": None,
        "description": None,
        "confidence": None,
        "occurrences": None,
        "examples": None,
        "metadata": None
    }
    assert instance.to_dict() == expected_output

def test_to_dict_error_case_invalid_input():
    # This case is not applicable as the function does not explicitly raise errors for invalid inputs.
    pass