import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import List

# Assuming the class name is CodeReader and it's part of a module named code_reader
from neural_engine.specialized_systems.code_reader import CodeReader

@pytest.fixture
def code_reader_instance(tmp_path):
    class MockCodeReader(CodeReader):
        def __init__(self, project_root: Path):
            super().__init__()
            self.project_root = project_root

    # Create a temporary directory to simulate the project root
    project_root = tmp_path / "project"
    project_root.mkdir()
    return MockCodeReader(project_root)

def test_list_python_files_happy_path(code_reader_instance):
    # Create some .py files in the project root
    (code_reader_instance.project_root / "file1.py").touch()
    (code_reader_instance.project_root / "subdir").mkdir()
    (code_reader_instance.project_root / "subdir" / "file2.py").touch()

    result = code_reader_instance.list_python_files()
    assert len(result) == 2
    assert (code_reader_instance.project_root / "file1.py") in result
    assert (code_reader_instance.project_root / "subdir" / "file2.py") in result

def test_list_python_files_empty_directory(code_reader_instance):
    result = code_reader_instance.list_python_files()
    assert len(result) == 0

def test_list_python_files_none_directory(code_reader_instance):
    result = code_reader_instance.list_python_files(None)
    assert len(result) == 0

def test_list_python_files_invalid_directory(code_reader_instance):
    with pytest.raises(ValueError):
        code_reader_instance.list_python_files("/nonexistent/path")

def test_list_python_files_skip_special_directories(code_reader_instance):
    (code_reader_instance.project_root / "__pycache__").mkdir()
    (code_reader_instance.project_root / "__pycache__" / "file.py").touch()
    (code_reader_instance.project_root / "venv").mkdir()
    (code_reader_instance.project_root / "venv" / "file.py").touch()

    result = code_reader_instance.list_python_files()
    assert len(result) == 0

@patch('neural_engine.specialized_systems.code_reader.logger')
def test_list_python_files_logger(mock_logger, code_reader_instance):
    (code_reader_instance.project_root / "file.py").touch()
    result = code_reader_instance.list_python_files()
    mock_logger.info.assert_called_once_with(f"Found {len(result)} Python files in {code_reader_instance.project_root}")

def test_list_python_files_relative_path(code_reader_instance):
    relative_path = Path("relative/subdir")
    (code_reader_instance.project_root / relative_path).mkdir(parents=True)
    (code_reader_instance.project_root / relative_path / "file.py").touch()

    result = code_reader_instance.list_python_files(relative_path)
    assert len(result) == 1
    assert (code_reader_instance.project_root / relative_path / "file.py") in result