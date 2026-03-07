import pytest
from neural_engine.input_router import InputRouter, AttentionMechanism, FilterSystem

def test_init_happy_path():
    # Arrange
    input_router = InputRouter()
    
    # Act & Assert
    assert isinstance(input_router.attention, AttentionMechanism)
    assert isinstance(input_router.filters, FilterSystem)
    assert "InputRouter initialized." in caplog.text

def test_init_edge_cases(caplog):
    # Arrange
    class MockAttention:
        def __init__(self):
            pass
    
    class MockFilterSystem:
        def __init__(self):
            pass
    
    InputRouter.attention = MockAttention()
    InputRouter.filters = MockFilterSystem()
    
    input_router = InputRouter()
    
    # Act & Assert
    assert isinstance(input_router.attention, MockAttention)
    assert isinstance(input_router.filters, MockFilterSystem)
    assert "InputRouter initialized." in caplog.text

def test_init_error_cases(caplog):
    # Arrange
    class InvalidAttention:
        def __init__(self):
            raise ValueError("Invalid attention mechanism")
    
    InputRouter.attention = InvalidAttention()
    
    with pytest.raises(ValueError) as exc_info:
        input_router = InputRouter()
    
    assert "Invalid attention mechanism" in str(exc_info.value)
    assert "InputRouter initialized." not in caplog.text

def test_init_async_behavior(caplog):
    # Arrange
    class AsyncAttention:
        async def __aenter__(self):
            pass
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    InputRouter.attention = AsyncAttention()
    
    input_router = InputRouter()
    
    # Act & Assert
    assert isinstance(input_router.attention, AsyncAttention)
    assert "InputRouter initialized." in caplog.text