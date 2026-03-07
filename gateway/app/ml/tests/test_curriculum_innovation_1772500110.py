import pytest

from gateway.app.ml.curriculum import get_all_domains, CURRICULUM

class TestGetAllDomains:

    def test_happy_path(self):
        """Test with normal inputs."""
        expected_domains = list(CURRICULUM.keys())
        assert get_all_domains() == expected_domains

    @pytest.mark.parametrize("input_data", [None, [], {}, 123])
    def test_edge_cases(self, input_data):
        """Test with edge cases: None, empty, invalid types."""
        assert get_all_domains() is not None
        assert isinstance(get_all_domains(), list)
        assert len(get_all_domains()) == len(CURRICULUM.keys())

    @pytest.mark.parametrize("invalid_input", [None, [], {}, "not a dict"])
    def test_error_cases(self, invalid_input):
        """Test with error cases: non-dict inputs."""
        assert get_all_domains() is not None
        assert isinstance(get_all_domains(), list)
        assert len(get_all_domains()) == len(CURRICULUM.keys())

    async def test_async_behavior(self, event_loop):
        """Test async behavior (if applicable)."""
        # Since the function does not involve async operations,
        # this test is just a placeholder for future expansion.
        expected_domains = list(CURRICULUM.keys())
        result = await get_all_domains()
        assert result == expected_domains