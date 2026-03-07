import pytest

from neural_engine.specialized_systems.dependency_mapper import DependencyMapper

def test_add_file_dependencies_happy_path():
    mapper = DependencyMapper()
    file_path = "test.py"
    imports = [
        {"type": "import", "module": "os"},
        {"type": "from_import", "module": "sys"}
    ]
    mapper.add_file_dependencies(file_path, imports)
    assert mapper.dependency_graph[file_path] == {"os", "sys"}

def test_add_file_dependencies_empty_imports():
    mapper = DependencyMapper()
    file_path = "test.py"
    imports = []
    mapper.add_file_dependencies(file_path, imports)
    assert mapper.dependency_graph[file_path] == set()

def test_add_file_dependencies_none_imports():
    mapper = DependencyMapper()
    file_path = "test.py"
    mapper.add_file_dependencies(file_path, None)
    assert mapper.dependency_graph[file_path] == set()

def test_add_file_dependencies_invalid_import_type():
    mapper = DependencyMapper()
    file_path = "test.py"
    imports = [
        {"type": "invalid", "module": "os"}
    ]
    mapper.add_file_dependencies(file_path, imports)
    assert mapper.dependency_graph[file_path] == set()

def test_add_file_dependencies_existing_file_path():
    mapper = DependencyMapper()
    file_path = "test.py"
    imports1 = [
        {"type": "import", "module": "os"}
    ]
    mapper.add_file_dependencies(file_path, imports1)
    assert mapper.dependency_graph[file_path] == {"os"}

    imports2 = [
        {"type": "from_import", "module": "sys"}
    ]
    mapper.add_file_dependencies(file_path, imports2)
    assert mapper.dependency_graph[file_path] == {"os", "sys"}

def test_add_file_dependencies_no_module():
    mapper = DependencyMapper()
    file_path = "test.py"
    imports = [
        {"type": "from_import", "module": ""}
    ]
    mapper.add_file_dependencies(file_path, imports)
    assert mapper.dependency_graph[file_path] == set()

def test_add_file_dependencies_null_string():
    mapper = DependencyMapper()
    file_path = None
    imports = [
        {"type": "import", "module": "os"}
    ]
    mapper.add_file_dependencies(file_path, imports)
    assert mapper.dependency_graph == {}

def test_add_file_dependencies_empty_string():
    mapper = DependencyMapper()
    file_path = ""
    imports = [
        {"type": "import", "module": "os"}
    ]
    mapper.add_file_dependencies(file_path, imports)
    assert mapper.dependency_graph == {}