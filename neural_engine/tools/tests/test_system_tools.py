import pytest
from unittest.mock import patch, MagicMock
from neural_engine.tools.system_tools import exec_python
from neural_engine.code_executor import CodeExecutor

# Mocking the CodeExecutor
class MockCodeExecutor:
    def __init__(self, timeout):
        self.timeout = timeout
    
    def execute(self, code):
        if "raise Exception" in code:
            raise RuntimeError("Simulated runtime error")
        elif "return 42" in code:
            return "Output: 42"
        elif "invalid syntax" in code:
            return "Error: invalid syntax"
        else:
            return "Success: executed"

# Patching the CodeExecutor
@pytest.fixture(autouse=True)
def mock_code_executor():
    with patch('neural_engine.tools.system_tools.CodeExecutor', new=MockCodeExecutor):
        yield

# Test cases
def test_exec_python_happy_path():
    code = "print('Hello, world!')"
    result = exec_python(code)
    assert result["success"]
    assert "Output: 42" != result["output"]  # Since we're not returning 42 in this case
    assert "✅ نجاح" in result["summary_ar"]

def test_exec_python_empty_code():
    code = ""
    result = exec_python(code)
    assert not result["success"]
    assert "يجب تحديد الكود" in result["error"]
    assert "لم يتم تحديد كود Python" in result["summary_ar"]

def test_exec_python_none_code():
    code = None
    result = exec_python(code)
    assert not result["success"]
    assert "يجب تحديد الكود" in result["error"]
    assert "لم يتم تحديد كود Python" in result["summary_ar"]

def test_exec_python_invalid_syntax():
    code = "invalid syntax"
    result = exec_python(code)
    assert not result["success"]
    assert "Error: invalid syntax" in result["output"]
    assert "❌ فشل" in result["summary_ar"]

def test_exec_python_runtime_error():
    code = "raise Exception('Simulated runtime error')"
    result = exec_python(code)
    assert not result["success"]
    assert "Runtime Error" in result["output"]
    assert "❌ فشل" in result["summary_ar"]

def test_exec_python_return_value():
    code = "return 42"
    result = exec_python(code)
    assert result["success"]
    assert "Output: 42" in result["output"]
    assert "✅ نجاح" in result["summary_ar"]

# No async behavior to test in this function