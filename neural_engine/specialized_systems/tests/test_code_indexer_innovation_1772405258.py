import pytest

from neural_engine.specialized_systems.code_indexer import CodeIndexer

@pytest.fixture
def code_indexer():
    indexer = CodeIndexer()
    indexer.function_index = {
        "function1": [{"file": "file1.py", "line": 10}],
        "function2": [{"file": "file2.py", "line": 20}]
    }
    return indexer

def test_find_function_happy_path(code_indexer):
    result = code_indexer.find_function("function1")
    assert result == [{"file": "file1.py", "line": 10}]

def test_find_function_empty_result(code_indexer):
    result = code_indexer.find_function("function3")
    assert result == []

def test_find_function_none_input(code_indexer):
    result = code_indexer.find_function(None)
    assert result == []

def test_find_function_empty_string_input(code_indexer):
    result = code_indexer.find_function("")
    assert result == []