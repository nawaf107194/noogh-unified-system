import pytest

class DependencyInjection:
    def __init__(self):
        self._dependencies = {
            "service1": "Service 1",
            "service2": "Service 2"
        }

    def get_dependency(self, dependency_name):
        if dependency_name not in self._dependencies:
            raise KeyError(f"Dependency '{dependency_name}' not found.")
        return self._dependencies[dependency_name]

def test_get_dependency_happy_path():
    di = DependencyInjection()
    assert di.get_dependency("service1") == "Service 1"
    assert di.get_dependency("service2") == "Service 2"

def test_get_dependency_edge_case_empty_input():
    di = DependencyInjection()
    with pytest.raises(KeyError) as exc_info:
        di.get_dependency("")
    assert str(exc_info.value) == "Dependency '' not found."

def test_get_dependency_edge_case_none_input():
    di = DependencyInjection()
    with pytest.raises(KeyError) as exc_info:
        di.get_dependency(None)
    assert str(exc_info.value) == "Dependency 'None' not found."

def test_get_dependency_error_case_invalid_input():
    di = DependencyInjection()
    with pytest.raises(KeyError) as exc_info:
        di.get_dependency("service3")
    assert str(exc_info.value) == "Dependency 'service3' not found."