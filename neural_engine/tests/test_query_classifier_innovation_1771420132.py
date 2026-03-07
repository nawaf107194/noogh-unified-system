import pytest
from unittest.mock import MagicMock
from typing import Dict

# Assuming the class is named QueryClassifier for the sake of this example
class MockQueryClassifier:
    def __init__(self):
        self.classify = MagicMock(return_value="general")
        self.is_mathematical = MagicMock(return_value=False)
        self.requires_strict_mode = MagicMock(return_value=False)
        self.math_keywords = ["math", "calculate", "sum"]

@pytest.fixture
def query_classifier():
    return MockQueryClassifier()

def test_get_classification_details_happy_path(query_classifier):
    query = "What is the capital of France?"
    expected_output = {
        "query": query,
        "classification": "general",
        "is_mathematical": False,
        "requires_strict": False,
        "detected_keywords": []
    }
    assert query_classifier.get_classification_details(query) == expected_output

def test_get_classification_details_edge_case_empty_query(query_classifier):
    query = ""
    expected_output = {
        "query": query,
        "classification": "general",
        "is_mathematical": False,
        "requires_strict": False,
        "detected_keywords": []
    }
    assert query_classifier.get_classification_details(query) == expected_output

def test_get_classification_details_edge_case_none_query(query_classifier):
    with pytest.raises(TypeError):
        query_classifier.get_classification_details(None)

def test_get_classification_details_error_case_invalid_input(query_classifier):
    with pytest.raises(TypeError):
        query_classifier.get_classification_details(123)

def test_get_classification_details_with_mathematical_keywords(query_classifier):
    query = "Calculate the sum of 5 and 7"
    expected_output = {
        "query": query,
        "classification": "general",
        "is_mathematical": False,
        "requires_strict": False,
        "detected_keywords": ["calculate", "sum"]
    }
    assert query_classifier.get_classification_details(query) == expected_output

# Since the function is not asynchronous, there's no need to test async behavior.
# If it were asynchronous, you would use pytest-asyncio or similar to write tests.