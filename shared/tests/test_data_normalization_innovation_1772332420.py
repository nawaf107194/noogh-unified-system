import pytest

from shared.data_normalization import DataNormalizer, normalize

class TestDataNormalizer:

    @pytest.mark.parametrize("input_data, expected_output", [
        ({"a": 1, "b": 2}, {"a": 1, "b": 2}),  # Normal dictionary input
        ([1, 2, 3], [1, 2, 3]),  # Normal list input
        ({"a": {"b": 2}}, {"a": {"b": 2}}),  # Nested dictionary input
        ([{"a": 1}, {"b": 2}], [{"a": 1}, {"b": 2}]),  # List of dictionaries input
    ])
    def test_normalize_happy_path(self, input_data, expected_output):
        result = normalize(input_data)
        assert result == expected_output

    @pytest.mark.parametrize("input_data", [
        None,  # Input is None
        [],  # Empty list
        {},  # Empty dictionary
        "not a dict or list",  # Invalid input type
    ])
    def test_normalize_edge_cases(self, input_data):
        result = normalize(input_data)
        assert result is None

    @pytest.mark.parametrize("input_data, expected_output", [
        (123, None),  # Integer input
        "string",  # String input
        True,  # Boolean input
        bytes(10),  # Bytes input
    ])
    def test_normalize_error_cases(self, input_data, expected_output):
        result = normalize(input_data)
        assert result == expected_output

    @pytest.mark.asyncio
    async def test_async_behavior(self):
        data_normalizer = DataNormalizer()
        normalized_data = await data_normalizer.normalize({"a": 1, "b": 2})
        assert normalized_data == {"a": 1, "b": 2}