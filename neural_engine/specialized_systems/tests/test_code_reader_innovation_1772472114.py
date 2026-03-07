import pytest
from pathlib import Path
from typing import List, Dict, Any

class MockCodeReader:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.files_to_return = []

    def list_python_files(self, directory: str) -> List[Path]:
        if directory in [None, ""]:
            return []
        return [Path(directory) / f for f in self.files_to_return]

def test_search_in_files_happy_path(mocker):
    reader = MockCodeReader("/home/noogh/projects/noogh_unified_system")
    reader.files_to_return = ["file1.py", "file2.py"]

    with open("file1.py", "w") as f:
        f.write("import os\nprint('hello')\n")

    with open("file2.py", "w") as f:
        f.write("def foo():\n    return 42\n")

    pattern = "print"
    result = reader.search_in_files(pattern)
    
    assert len(result) == 1
    assert result[0] == {
        "file": Path("file1.py").relative_to("/home/noogh/projects/noogh_unified_system"),
        "line": 2,
        "content": "print('hello')",
    }

def test_search_in_files_empty_directory(mocker):
    reader = MockCodeReader("/home/noogh/projects/noogh_unified_system")
    reader.files_to_return = []

    pattern = "import"
    result = reader.search_in_files(pattern, "/nonexistent_dir")

    assert len(result) == 0

def test_search_in_files_non_existent_directory(mocker):
    reader = MockCodeReader("/home/noogh/projects/noogh_unified_system")
    reader.files_to_return = []

    pattern = "import"
    with pytest.raises(FileNotFoundError):
        reader.search_in_files(pattern, "/nonexistent_dir")

def test_search_in_files_invalid_pattern_type(mocker):
    reader = MockCodeReader("/home/noogh/projects/noogh_unified_system")
    reader.files_to_return = ["file1.py"]

    pattern = 123
    result = reader.search_in_files(pattern)

    assert len(result) == 0

def test_search_in_files_invalid_directory_type(mocker):
    reader = MockCodeReader("/home/noogh/projects/noogh_unified_system")
    reader.files_to_return = ["file1.py"]

    pattern = "import"
    with pytest.raises(TypeError):
        reader.search_in_files(pattern, 123)

def test_search_in_files_no_match(mocker):
    reader = MockCodeReader("/home/noogh/projects/noogh_unified_system")
    reader.files_to_return = ["file1.py"]

    with open("file1.py", "w") as f:
        f.write("import os\nprint('hello')\n")

    pattern = "not_found"
    result = reader.search_in_files(pattern)

    assert len(result) == 0