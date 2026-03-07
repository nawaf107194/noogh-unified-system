import pytest
from unittest.mock import patch, MagicMock
from neural_engine.autonomy.code_doctor import CodeDoctor

@pytest.fixture
def code_doctor():
    return CodeDoctor()

@pytest.mark.parametrize("content, expected_found, expected_missing", [
    ("def hello():\n    print('Hello, world!')", ["Python function"], []),
    ("import os\nprint(os.getcwd())", [], ["Python module"]),
    ("\ndef foo():\n    pass", ["Python function"], ["Python module"]),
    ("", [], []),
    (None, [], []),
])
def test_check_patterns_happy_path(code_doctor, content, expected_found, expected_missing):
    result = code_doctor._check_patterns(content)
    assert result == (expected_found, expected_missing)

@pytest.mark.parametrize("content, expected_found, expected_missing", [
    ("def hello():\n    print('Hello, world!')\ndef goodbye():\n    print('Goodbye, world!')",
     ["Python function", "Python function"], []),
    ("import os\nimport sys", [], ["Python module", "Python module"]),
    ("\ndef foo():\n    pass\ndef bar():\n    pass", ["Python function", "Python function"], ["Python module", "Python module"]),
])
def test_check_patterns_multiple_patterns(code_doctor, content, expected_found, expected_missing):
    result = code_doctor._check_patterns(content)
    assert result == (expected_found, expected_missing)

@pytest.mark.parametrize("content, expected_found, expected_missing", [
    ("import numpy as np\nprint(np.array([1, 2, 3]))\nprint(np.mean([4, 5, 6]))",
     [], ["Python module"]),
])
def test_check_patterns_complex_pattern(code_doctor, content, expected_found, expected_missing):
    result = code_doctor._check_patterns(content)
    assert result == (expected_found, expected_missing)

@pytest.mark.parametrize("content, expected_found, expected_missing", [
    ("import os\nprint(os.getcwd())\ndef hello():\n    print('Hello, world!')",
     [], ["Python module"]),
])
def test_check_patterns_mixed_patterns(code_doctor, content, expected_found, expected_missing):
    result = code_doctor._check_patterns(content)
    assert result == (expected_found, expected_missing)

@pytest.mark.parametrize("content, expected_found, expected_missing", [
    ("import numpy as np\nnp.array([1, 2, 3])\nnp.mean([4, 5, 6])",
     [], ["Python module"]),
])
def test_check_patterns_no_pattern(code_doctor, content, expected_found, expected_missing):
    result = code_doctor._check_patterns(content)
    assert result == (expected_found, expected_missing)

@pytest.mark.parametrize("content, expected_found, expected_missing", [
    ("import os\nprint(os.getcwd())\ndef hello():\n    print('Hello, world!')",
     [], ["Python module"]),
])
def test_check_patterns_edge_case_empty_string(code_doctor, content, expected_found, expected_missing):
    result = code_doctor._check_patterns(content)
    assert result == (expected_found, expected_missing)

@pytest.mark.parametrize("content, expected_found, expected_missing", [
    ("import os\nprint(os.getcwd())\ndef hello():\n    print('Hello, world!')",
     [], ["Python module"]),
])
def test_check_patterns_edge_case_none(code_doctor, content, expected_found, expected_missing):
    result = code_doctor._check_patterns(content)
    assert result == (expected_found, expected_missing)