import pytest

class MockCodeIndexer:
    def __init__(self):
        self.function_index = {
            'example_function': [{'line': 10, 'file': 'test.py'}]
        }

    def find_function(self, function_name: str) -> List[Dict[str, Any]]:
        return self.function_index.get(function_name, [])

def test_find_function_happy_path():
    indexer = MockCodeIndexer()
    result = indexer.find_function('example_function')
    assert result == [{'line': 10, 'file': 'test.py'}]

def test_find_function_empty_input():
    indexer = MockCodeIndexer()
    result = indexer.find_function('')
    assert result == []

def test_find_function_none_input():
    indexer = MockCodeIndexer()
    result = indexer.find_function(None)
    assert result == []

def test_find_function_not_found():
    indexer = MockCodeIndexer()
    result = indexer.find_function('nonexistent_function')
    assert result == []