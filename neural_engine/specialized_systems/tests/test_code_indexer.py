import pytest
from unittest.mock import MagicMock, patch

# Mock the logger
logger = MagicMock()

class TestCodeIndexer:

    @pytest.fixture
    def indexer(self):
        class MockIndexer:
            def __init__(self):
                self.function_index = {}
                self.class_index = {}
                self.module_index = {}
        return MockIndexer()

    def test_happy_path(self, indexer):
        file_path = "/path/to/file.py"
        analysis = {
            "functions": [
                {"name": "func1", "line": 10, "args": ["arg1", "arg2"]},
                {"name": "func2", "line": 20, "args": ["arg3"]}
            ],
            "classes": [
                {"name": "Class1", "line": 30, "methods": ["method1", "method2"]}
            ]
        }
        
        indexer.index_file(file_path, analysis)
        
        assert indexer.function_index == {
            "func1": [{"file": file_path, "line": 10, "args": ["arg1", "arg2"]}],
            "func2": [{"file": file_path, "line": 20, "args": ["arg3"]}]
        }
        assert indexer.class_index == {
            "Class1": [{"file": file_path, "line": 30, "methods": ["method1", "method2"]}]
        }
        assert indexer.module_index == {file_path: analysis}
        logger.info.assert_called_once_with(f"Indexed {file_path}: 2 functions, 1 classes")

    def test_empty_analysis(self, indexer):
        file_path = "/path/to/empty_file.py"
        analysis = {"functions": [], "classes": []}
        
        indexer.index_file(file_path, analysis)
        
        assert indexer.function_index == {}
        assert indexer.class_index == {}
        assert indexer.module_index == {file_path: analysis}
        logger.info.assert_called_once_with(f"Indexed {file_path}: 0 functions, 0 classes")

    def test_none_analysis(self, indexer):
        file_path = "/path/to/none_file.py"
        analysis = None
        
        with pytest.raises(TypeError):
            indexer.index_file(file_path, analysis)

    def test_invalid_analysis(self, indexer):
        file_path = "/path/to/invalid_file.py"
        analysis = {"wrong_key": []}
        
        with pytest.raises(KeyError):
            indexer.index_file(file_path, analysis)

    def test_async_behavior(self, indexer):
        # Assuming there is no async behavior in the current implementation,
        # this test is more of a placeholder or can be used if future changes introduce async functionality.
        pass