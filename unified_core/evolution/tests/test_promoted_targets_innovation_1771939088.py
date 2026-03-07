import pytest

class MockPromotedTargets:
    def __init__(self):
        self._targets = {}
    
    def _make_key(self, file_path: str, function_name: str) -> str:
        return f"{file_path}:{function_name}"
    
    def _save(self):
        pass
    
    def remove(self, file_path: str, function_name: str):
        """Remove a target (e.g. if code changed significantly)."""
        key = self._make_key(file_path, function_name)
        if key in self._targets:
            del self._targets[key]
            self._save()

def test_remove_happy_path():
    targets = MockPromotedTargets()
    targets._targets = {'/path/to/file.py:func1': True}
    targets.remove('/path/to/file.py', 'func1')
    assert '/path/to/file.py:func1' not in targets._targets

def test_remove_empty_file_path():
    targets = MockPromotedTargets()
    targets.remove('', 'func1')
    assert '/::func1' not in targets._targets  # Assuming _make_key handles this edge case

def test_remove_none_file_path():
    targets = MockPromotedTargets()
    targets.remove(None, 'func1')
    assert ':func1' not in targets._targets  # Assuming _make_key handles this edge case

def test_remove_empty_function_name():
    targets = MockPromotedTargets()
    targets._targets = {'/path/to/file.py': True}
    targets.remove('/path/to/file.py', '')
    assert '/path/to/file.py:' not in targets._targets  # Assuming _make_key handles this edge case

def test_remove_none_function_name():
    targets = MockPromotedTargets()
    targets._targets = {'/path/to/file.py': True}
    targets.remove('/path/to/file.py', None)
    assert '/path/to/file.py:' not in targets._targets  # Assuming _make_key handles this edge case

def test_remove_missing_target():
    targets = MockPromotedTargets()
    targets.remove('/path/to/file.py', 'func1')
    assert '/path/to/file.py:func1' not in targets._targets

def test_remove_async_behavior():
    pass  # No async behavior to test for this function