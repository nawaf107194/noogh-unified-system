import pytest

from shared.dependency_resolver import DependencyResolver, visited, resolved_order, _module_dependencies, _loaded_modules

@pytest.fixture(autouse=True)
def reset_state():
    visited.clear()
    resolved_order.clear()
    _module_dependencies.clear()
    _loaded_modules.clear()

def test_visit_happy_path():
    resolver = DependencyResolver()
    
    # Set up dependencies
    _module_dependencies['A'] = ['B', 'C']
    _module_dependencies['B'] = []
    _module_dependencies['C'] = ['D']
    _module_dependencies['D'] = []
    
    resolver.visit('A')
    
    assert resolved_order == ['A', 'C', 'D', 'B']

def test_visit_empty_module_name():
    resolver = DependencyResolver()
    resolver.visit('')
    assert resolved_order == []

def test_visit_none_module_name():
    resolver = DependencyResolver()
    resolver.visit(None)
    assert resolved_order == []

def test_visit_module_not_in_dependencies():
    resolver = DependencyResolver()
    resolver.visit('A')
    assert resolved_order == ['A']

def test_visit_circular_dependency_error():
    resolver = DependencyResolver()
    
    # Set up circular dependency
    _module_dependencies['A'] = ['B']
    _module_dependencies['B'] = ['A']
    
    with pytest.raises(ValueError) as exc_info:
        resolver.visit('A')
    
    assert 'Circular dependency detected' in str(exc_info.value)

def test_visit_already_visited():
    resolver = DependencyResolver()
    
    # Set up dependencies
    _module_dependencies['A'] = []
    _module_dependencies['B'] = ['A']
    
    resolver.visit('A')
    resolver.visit('A')  # Should not visit 'A' again
    
    assert resolved_order == ['A', 'B']

def test_visit_with_async_behavior():
    resolver = DependencyResolver()
    
    async def mock_visit(module_name):
        await asyncio.sleep(0.1)
        resolver.visit(module_name)
    
    asyncio.run(mock_visit('A'))
    asyncio.run(mock_visit('B'))
    
    assert resolved_order == ['A', 'B']