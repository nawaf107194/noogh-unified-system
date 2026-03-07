import pytest
from your_module import DependencyMapper  # Import the real class

def test_add_file_dependencies_happy_path():
    mapper = DependencyMapper()
    file_path = "test.py"
    imports = [
        {"type": "import", "module": "os"},
        {"type": "from_import", "module": "sys"}
    ]
    mapper.add_file_dependencies(file_path, imports)
    assert file_path in mapper.dependency_graph
    assert 'os' in mapper.dependency_graph[file_path]
    assert 'sys' in mapper.dependency_graph[file_path]

def test_add_file_dependencies_empty_imports():
    mapper = DependencyMapper()
    file_path = "test.py"
    imports = []
    mapper.add_file_dependencies(file_path, imports)
    assert file_path in mapper.dependency_graph
    assert len(mapper.dependency_graph[file_path]) == 0

def test_add_file_dependencies_none_imports():
    mapper = DependencyMapper()
    file_path = "test.py"
    imports = None
    mapper.add_file_dependencies(file_path, imports)
    assert file_path not in mapper.dependency_graph

def test_add_file_dependencies_invalid_type_import():
    mapper = DependencyMapper()
    file_path = "test.py"
    imports = [
        {"type": "invalid", "module": "os"}
    ]
    mapper.add_file_dependencies(file_path, imports)
    assert file_path in mapper.dependency_graph
    assert len(mapper.dependency_graph[file_path]) == 0

def test_add_file_dependencies_invalid_module_from_import():
    mapper = DependencyMapper()
    file_path = "test.py"
    imports = [
        {"type": "from_import", "module": None}
    ]
    mapper.add_file_dependencies(file_path, imports)
    assert file_path in mapper.dependency_graph
    assert len(mapper.dependency_graph[file_path]) == 0

def test_add_file_dependencies_existing_file():
    mapper = DependencyMapper()
    file_path = "test.py"
    initial_imports = [
        {"type": "import", "module": "os"}
    ]
    mapper.add_file_dependencies(file_path, initial_imports)
    
    additional_imports = [
        {"type": "from_import", "module": "sys"}
    ]
    mapper.add_file_dependencies(file_path, additional_imports)
    
    assert file_path in mapper.dependency_graph
    assert 'os' in mapper.dependency_graph[file_path]
    assert 'sys' in mapper.dependency_graph[file_path]