import pytest
from pathlib import Path
from unittest.mock import patch

from neural_engine.specialized_systems.code_reader import CodeReader

@pytest.fixture
def code_reader():
    return CodeReader()

def test_list_python_files_happy_path(code_reader):
    with patch.object(CodeReader, 'project_root', new=Path('/test/project')):
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = [
                Path('/test/project/file1.py'),
                Path('/test/project/subdir/file2.py')
            ]
            result = code_reader.list_python_files()
    assert result == [Path('/test/project/file1.py'), Path('/test/project/subdir/file2.py')]
    logger.info.assert_called_once_with(f"Found 2 Python files in /test/project")

def test_list_python_files_empty_directory(code_reader):
    with patch.object(CodeReader, 'project_root', new=Path('/test/project')):
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = []
            result = code_reader.list_python_files()
    assert result == []
    logger.info.assert_called_once_with(f"Found 0 Python files in /test/project")

def test_list_python_files_directory_none(code_reader):
    with patch.object(CodeReader, 'project_root', new=Path('/test/project')):
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = [
                Path('/test/project/file1.py'),
                Path('/test/project/subdir/file2.py')
            ]
            result = code_reader.list_python_files(directory=None)
    assert result == [Path('/test/project/file1.py'), Path('/test/project/subdir/file2.py')]
    logger.info.assert_called_once_with(f"Found 2 Python files in /test/project")

def test_list_python_files_relative_path(code_reader):
    with patch.object(CodeReader, 'project_root', new=Path('/test/project')):
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = [
                Path('/test/project/subdir/file2.py')
            ]
            result = code_reader.list_python_files(directory='subdir')
    assert result == [Path('/test/project/subdir/file2.py')]
    logger.info.assert_called_once_with(f"Found 1 Python files in /test/project/subdir")

def test_list_python_files_invalid_directory(code_reader):
    with patch.object(CodeReader, 'project_root', new=Path('/test/project')):
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = []
            result = code_reader.list_python_files(directory='nonexistent')
    assert result == []
    logger.info.assert_called_once_with(f"Found 0 Python files in /test/project/nonexistent")

def test_list_python_files_skip_cache_and_venv(code_reader):
    with patch.object(CodeReader, 'project_root', new=Path('/test/project')):
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = [
                Path('/test/project/file1.py'),
                Path('/test/project/__pycache__/file2.cpython-38.pyc'),
                Path('/test/project/venv/lib/python3.8/site-packages/file3.py')
            ]
            result = code_reader.list_python_files()
    assert result == [Path('/test/project/file1.py'), Path('/test/project/venv/lib/python3.8/site-packages/file3.py')]
    logger.info.assert_called_once_with(f"Found 2 Python files in /test/project")