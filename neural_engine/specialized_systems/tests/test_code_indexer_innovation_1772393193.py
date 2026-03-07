import pytest

class MockCodeIndexer:
    def __init__(self):
        self.class_index = {
            'TestClass': [{'file': 'test_file.py', 'line': 10}],
            'AnotherClass': [{'file': 'another_file.py', 'line': 20}]
        }

    def find_class(self, class_name: str) -> List[Dict[str, Any]]:
        return self.class_index.get(class_name, [])

@pytest.fixture
def code_indexer():
    return MockCodeIndexer()

def test_find_class_happy_path(code_indexer):
    result = code_indexer.find_class('TestClass')
    assert result == [{'file': 'test_file.py', 'line': 10}]

def test_find_class_empty(code_indexer):
    result = code_indexer.find_class('')
    assert result == []

def test_find_class_none(code_indexer):
    result = code_indexer.find_class(None)
    assert result == []

def test_find_class_non_existent(class_indexer):
    result = class_indexer.find_class('NonExistentClass')
    assert result == []