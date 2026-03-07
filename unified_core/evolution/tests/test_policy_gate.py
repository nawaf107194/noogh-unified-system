import pytest
from unified_core.evolution.policy_gate import PolicyGate

@pytest.fixture
def policy_gate():
    return PolicyGate()

@pytest.mark.parametrize("path, patterns, expected", [
    ("/home/user/log.txt", (".txt", ".log"), True),
    ("/data/temp/file.csv", ("*.csv", "*.json"), False),
    ("/image.png", (".png", ".jpg"), True),
    ("/project/src/main.py", ("*.py",), True),
    ("/config.ini", (".ini",), True),
    ("/unknown_extension", (), False),
    ("", (".txt",), False),
    (None, (".txt",), False),
    ("/boundary_case/", (".csv", ""), False),
])
def test_matches_pattern(policy_gate, path, patterns, expected):
    result = policy_gate._matches_pattern(path, patterns)
    assert result == expected

@pytest.mark.parametrize("path, patterns", [
    ("/home/user/log.txt", {None}),
    ("", {"*.txt"}),
    (None, [".txt"]),
    ((123, 456), (".txt")),
])
def test_matches_pattern_with_invalid_inputs(policy_gate, path, patterns):
    result = policy_gate._matches_pattern(path, patterns)
    assert result is False