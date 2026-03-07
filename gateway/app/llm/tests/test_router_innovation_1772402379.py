import pytest

from gateway.app.llm.router import _needs_cloud_capabilities

class TestNeedsCloudCapabilities:

    @pytest.mark.parametrize("prompt, expected", [
        ("latest news", True),
        ("search web", True),
        ("current events", True),
        ("weather", True),
        ("no cloud needed", False),
        ("", False),
        (None, False)
    ])
    def test_happy_path_and_edge_cases(self, prompt, expected):
        result = _needs_cloud_capabilities(prompt)
        assert result == expected

    @pytest.mark.parametrize("prompt, expected", [
        ([], False),
        ({}, False),
        (123, False),
        (True, False),
        ("   ", False),
        ("latest  news", True),
        ("search web  ", True),
        (" current events ", True),
        ("weather ", True)
    ])
    def test_error_cases_and_async_behavior(self, prompt, expected):
        result = _needs_cloud_capabilities(prompt)
        assert result == expected