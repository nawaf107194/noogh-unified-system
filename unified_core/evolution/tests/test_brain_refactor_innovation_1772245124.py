import pytest

from unified_core.evolution.brain_refactor import BrainRefactor

class TestExtractCodeFromResponse:
    def setup_method(self):
        self.brain = BrainRefactor()

    @pytest.mark.parametrize("response, expected", [
        ("def test():\n    print('Hello')", "def test():\n    print('Hello')"),
        ("async def test_async():\n    await asyncio.sleep(1)", "async def test_async():\n    await asyncio.sleep(1)"),
        ("import os\nfrom sys import path\npath.append('/home/noogh/projects/noogh_unified_system')\ndef foo():\n    pass", "def foo():\n    pass"),
        ("class MyClass:\n    def __init__(self):\n        pass\n    def method(self):\n        pass", "def method(self):\n        pass")
    ])
    def test_happy_path(self, response, expected):
        result = self.brain._extract_code_from_response(response)
        assert result == expected

    @pytest.mark.parametrize("response, expected", [
        ("", ""),
        (None, ""),
        ("This is not code", ""),
        ("\n\n\n\n\n\n", "")
    ])
    def test_edge_cases(self, response, expected):
        result = self.brain._extract_code_from_response(response)
        assert result == expected

    @pytest.mark.parametrize("response, expected_indent, expected_result", [
        ("def foo():\n    print('Hello')", 4, "def foo():\n    print('Hello')"),
        ("\tasync def bar():\n\t\tawait asyncio.sleep(1)", 0, "async def bar():\n\tawait asyncio.sleep(1)")
    ])
    def test_expected_indent(self, response, expected_indent, expected_result):
        result = self.brain._extract_code_from_response(response, expected_indent=expected_indent)
        assert result == expected_result

    @pytest.mark.parametrize("response", [
        ("def foo():\n    print('Hello'", "missing closing '"),
        ("import os\nfrom sys import path\npath.append('/home/noogh/projects/noogh_unified_system')", "truncated output"),
        ("\ndef foo():\n    pass\n\nasync def bar():\n    await asyncio.sleep(1)", "multiple function definitions")
    ])
    def test_error_cases(self, response):
        result = self.brain._extract_code_from_response(response)
        assert result == ""

    @pytest.mark.asyncio
    async def test_async_behavior(self):
        async def async_function():
            return "async def foo():\n    await asyncio.sleep(1)"
        
        response = await async_function()
        result = self.brain._extract_code_from_response(response)
        assert result == "async def foo():\n    await asyncio.sleep(1)"