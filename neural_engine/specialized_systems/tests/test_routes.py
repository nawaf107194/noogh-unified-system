import pytest

from neural_engine.specialized_systems.routes import get_self_improvement
from neural_engine.specialized_systems.self_improvement import SelfImprovementEngine

@pytest.fixture(autouse=True)
def reset_self_improvement():
    global _self_improvement
    _self_improvement = None

def test_get_self_improvement_happy_path(monkeypatch):
    # Mock the creation of SelfImprovementEngine
    mock_engine = Mock(spec=SelfImprovementEngine)
    monkeypatch.setattr('neural_engine.specialized_systems.routes.SelfImprovementEngine', Mock(return_value=mock_engine))
    
    # Call the function
    result = get_self_improvement()
    
    # Assertions
    assert result is not None
    mock_engine.assert_called_once()

def test_get_self_improvement_first_call(monkeypatch):
    # Mock the creation of SelfImprovementEngine
    mock_engine = Mock(spec=SelfImprovementEngine)
    monkeypatch.setattr('neural_engine.specialized_systems.routes.SelfImprovementEngine', Mock(return_value=mock_engine))
    
    # Call the function twice to ensure it's a singleton
    result1 = get_self_improvement()
    result2 = get_self_improvement()
    
    # Assertions
    assert result1 is result2
    mock_engine.assert_called_once()

def test_get_self_improvement_no_mock():
    # Call the function without mocking
    result = get_self_improvement()
    
    # Assertions
    assert result is not None