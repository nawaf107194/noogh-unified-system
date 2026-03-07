import pytest
from typing import List, Dict, Any
from neural_engine.specialized_systems.dependency_mapper import DependencyMapper

@pytest.fixture
def mapper():
    return DependencyMapper()

def test_add_file_dependencies_happy_path(mapper):
    file_path = "/path/to/file.py"
    imports = [
        {"type": "import", "module": "os"},
        {"type": "from_import", "module": "json"}
    ]
    mapper.add_file_dependencies(file_path, imports)
    assert file_path in mapper.dependency_graph
    assert mapper.dependency_graph[file_path] == {'os', 'json'}

def test_add_file_dependencies_empty_imports(mapper):
    file_path = "/path/to/file.py"
    imports = []
    mapper.add_file_dependencies(file_path, imports)
    assert file_path in mapper.dependency_graph
    assert mapper.dependency_graph[file_path] == set()

def test_add_file_dependency_none_value(mapper):
    with pytest.raises(TypeError) as exc_info:
        mapper.add_file_dependencies(None, [])
    assert str(exc_info.value) == "file_path cannot be None"

def test_add_file_dependency_empty_string(mapper):
    with pytest.raises(ValueError) as exc_info:
        mapper.add_file_dependencies("", [])
    assert str(exc_info.value) == "file_path cannot be an empty string"

def test_add_file_dependency_invalid_import_type(mapper):
    file_path = "/path/to/file.py"
    imports = [{"type": "unknown", "module": "os"}]
    with pytest.raises(ValueError) as exc_info:
        mapper.add_file_dependencies(file_path, imports)
    assert str(exc_info.value).startswith("Invalid import type")

def test_add_file_dependency_missing_module(mapper):
    file_path = "/path/to/file.py"
    imports = [{"type": "from_import", "module": None}]
    with pytest.raises(ValueError) as exc_info:
        mapper.add_file_dependencies(file_path, imports)
    assert str(exc_info.value).startswith("Module cannot be None when import type is from_import")