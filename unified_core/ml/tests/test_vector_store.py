import pytest

from unified_core.ml.vector_store import VectorStore  # Assuming VectorStore is the class name

@pytest.fixture
def vector_store():
    # Mock or initialize your VectorStore instance here
    # This is just a placeholder; you should replace it with actual initialization logic
    return VectorStore()

class TestGetBestMatch:

    @pytest.mark.parametrize("query, threshold, expected", [
        ("search documents", 0.3, "document_search"),  # Normal input
        ("find images", 0.5, "image_finder"),          # Another normal input
    ])
    def test_happy_path(self, vector_store, query, threshold, expected):
        result = vector_store.get_best_match(query, threshold)
        assert result == expected

    @pytest.mark.parametrize("query, threshold", [
        ("", 0.3),  # Empty string
        (None, 0.3),  # None as input
        ("boundary_case", 0),  # Threshold at boundary
        ("boundary_case", 1),  # Another boundary case
    ])
    def test_edge_cases(self, vector_store, query, threshold):
        result = vector_store.get_best_match(query, threshold)
        assert result is None  # Assuming no match for edge cases

    @pytest.mark.parametrize("query, threshold", [
        (123, 0.3),  # Non-string query
        ("valid_query", -0.1),  # Negative threshold
        ("valid_query", 1.1),  # Threshold greater than 1
    ])
    def test_error_cases(self, vector_store, query, threshold):
        with pytest.raises(TypeError):  # Adjust exception type based on your implementation
            vector_store.get_best_match(query, threshold)

    # If the method supports async behavior, add this test
    @pytest.mark.asyncio
    async def test_async_behavior(self, vector_store):
        result = await vector_store.get_best_match("async_query", 0.3)
        assert result == "expected_tool_name"  # Replace with actual expected tool name