import pytest

from unified_core.ml.vector_store import get_best_match

class MockVectorStore:
    @staticmethod
    def match(query, n_results=1, threshold=0.3):
        if query == "happy_path":
            return [{"tool_name": "happy_tool"}]
        elif query == "edge_case_empty":
            return []
        elif query == "edge_case_none":
            return None
        elif query == "error_case_invalid_input":
            raise ValueError("Invalid input")
        else:
            return [{"tool_name": "default_tool"}]

@pytest.fixture
def vector_store():
    return MockVectorStore()

def test_get_best_match_happy_path(vector_store):
    assert get_best_match(vector_store, "happy_path") == "happy_tool"

def test_get_best_match_edge_case_empty(vector_store):
    assert get_best_match(vector_store, "edge_case_empty") is None

def test_get_best_match_edge_case_none(vector_store):
    with pytest.raises(ValueError) as exc_info:
        get_best_match(vector_store, "edge_case_none")
    assert str(exc_info.value) == "Invalid input"

def test_get_best_match_error_case_invalid_input(vector_store):
    with pytest.raises(ValueError) as exc_info:
        get_best_match(vector_store, "error_case_invalid_input")
    assert str(exc_info.value) == "Invalid input"