import pytest

from gateway.app.core.tools_extended import _analyze_code


@pytest.mark.parametrize("code, expected_output", [
    (
        "def foo():\n    pass\n",
        "Lines: 3\nFunctions: 1\nClasses: 0\nComplexity: 0\n"
        "Functions:\n  - foo() [2 lines]",
    ),
    (
        "class Bar:\n    def baz(self):\n        pass\n",
        "Lines: 4\nFunctions: 0\nClasses: 1\nComplexity: 0\n"
        "Classes:\n  - Bar\n",
    ),
    (
        "def foo():\n    pass\n\ndef bar():\n    pass\n",
        "Lines: 5\nFunctions: 2\nClasses: 0\nComplexity: 0\n"
        "Functions:\n  - foo() [2 lines]\n  - bar() [2 lines]",
    ),
])
def test_happy_path(code, expected_output):
    result = _analyze_code(code)
    assert result == expected_output


@pytest.mark.parametrize("code", [
    "",
    None,
    "import os\n",
])
def test_edge_cases(code):
    result = _analyze_code(code)
    assert result.startswith("Analysis Error:")


@pytest.mark.parametrize("code, expected_error", [
    (
        "invalid code",
        "function not defined",
    ),
    (
        "def foo(\n",
        "incomplete input",
    ),
])
def test_error_cases(code, expected_error):
    result = _analyze_code(code)
    assert f"Analysis Error: {expected_error}" in result


@pytest.mark.asyncio
async def test_async_behavior():
    import asyncio

    async def analyze_code_mock(code):
        if code == "await asyncio.sleep(1)\n":
            return {"success": True, "lines": 2, "functions": [], "classes": [], "complexity": 0}
        else:
            return {"success": False, "error": "invalid input"}

    original_analyze_code = _analyze_code.__globals__['analyze_code']
    _analyze_code.__globals__['analyze_code'] = analyze_code_mock

    try:
        result = await _analyze_code("await asyncio.sleep(1)\n")
        assert result == "Lines: 2\nFunctions: 0\nClasses: 0\nComplexity: 0"
    finally:
        _analyze_code.__globals__['analyze_code'] = original_analyze_code