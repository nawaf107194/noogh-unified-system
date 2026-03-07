import pytest

class DependencyMapperMock:
    def __init__(self):
        self.dependency_graph = {
            'module1': ['file1.py', 'file2.py'],
            'module2': ['file3.py']
        }

    def get_dependents(self, module_name: str) -> List[str]:
        """
        Get all files that depend on a module

        Args:
            module_name: Name of module

        Returns:
            List of file paths
        """
        dependents = []
        for file_path, deps in self.dependency_graph.items():
            if module_name in deps:
                dependents.append(file_path)

        return dependents

@pytest.fixture
def dependency_mapper():
    return DependencyMapperMock()

def test_get_dependents_happy_path(dependency_mapper):
    assert dependency_mapper.get_dependents('module1') == ['file1.py', 'file2.py']
    assert dependency_mapper.get_dependents('module2') == ['file3.py']

def test_get_dependents_empty_dependency_graph(dependency_mapper):
    dependency_mapper.dependency_graph = {}
    assert dependency_mapper.get_dependents('module1') == []

def test_get_dependents_module_not_found(dependency_mapper):
    assert dependency_mapper.get_dependents('nonexistent_module') == []