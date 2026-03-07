import pytest

class MockPromotedTargets:
    def __init__(self):
        self._targets = set()

    def _make_key(self, file_path: str, function_name: str) -> str:
        return f"{file_path}:{function_name}"

    def contains(self, file_path: str, function_name: str) -> bool:
        """Check if a target has already been promoted."""
        key = self._make_key(file_path, function_name)
        return key in self._targets

@pytest.fixture
def promoted_targets():
    pt = MockPromotedTargets()
    pt._targets.add("src/main.py:test_function")
    return pt

def test_contains_happy_path(promoted_targets):
    assert promoted_targets.contains("src/main.py", "test_function") == True

def test_contains_not_found(promoted_targets):
    assert promoted_targets.contains("src/main.py", "another_function") == False

def test_contains_empty_strings(promoted_targets):
    assert promoted_targets.contains("", "") == False

def test_contains_none_inputs(promoted_targets):
    with pytest.raises(TypeError):
        promoted_targets.contains(None, None)

def test_contains_invalid_input_types(promoted_targets):
    with pytest.raises(TypeError):
        promoted_targets.contains(123, 456)

def test_contains_boundary_cases(promoted_targets):
    assert promoted_targets.contains("a" * 1000, "b" * 1000) == False

# Since the method does not have any asynchronous behavior, there's no need to test async behavior.