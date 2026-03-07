import pytest
import os
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_components():
    return (
        MagicMock(spec='neural_engine.reasoning_engine.ReasoningEngine'),
        MagicMock(spec='neural_engine.memory_manager.MemoryManager'),
        MagicMock(spec='neural_engine.recall_engine.RecallEngine'),
        MagicMock(spec='neural_engine.nlp_processor.NLPProcessor'),
        MagicMock(spec='neural_engine.shell_executor.ShellExecutor'),
        MagicMock(spec='neural_engine.image_processor.ImageProcessor'),
        MagicMock(spec='neural_engine.dream_processor.DreamProcessor')
    )

@pytest.fixture
def mock_model_authority():
    authority = MagicMock()
    authority.loaded_model = 'test_model'
    authority.loaded_tokenizer = 'test_tokenizer'
    return authority

@pytest fixture
def mock_logger():
    with patch('neural_engine.api.routes.logger') as mock:
        yield mock

def test_get_components_happy_path(mock_components, mock_model_authority, mock_logger):
    global _components_cache, _components_lock
    
    _components_cache = None
    _components_lock = MagicMock()
    
    with patch('neural_engine.api.routes.get_model_authority', return_value=mock_model_authority) as mock_get_authority:
        components = get_components()
        
        assert components == mock_components
        assert isinstance(components[0], type(mock_components[0]))
        assert mock_logger.info.called_once_with("🔧 Initializing neural components (first request)...")
        assert _components_cache is not None

def test_get_components_first_request_caching(mock_components, mock_model_authority, mock_logger):
    global _components_cache, _components_lock
    
    _components_cache = mock_components
    _components_lock = MagicMock()
    
    with patch('neural_engine.api.routes.get_model_authority', return_value=mock_model_authority) as mock_get_authority:
        components = get_components()
        
        assert components == mock_components
        assert not mock_logger.info.called
        assert _components_cache is not None

def test_get_components_model_already_loaded(mock_components, mock_model_authority, mock_logger):
    global _components_cache, _components_lock
    
    _components_cache = None
    _components_lock = MagicMock()
    
    with patch('neural_engine.api.routes.get_model_authority', return_value=mock_model_authority) as mock_get_authority:
        with patch('neural_engine.api.routes.ReasoningEngine') as MockReasoningEngine:
            MockReasoningEngine.return_value = mock_components[0]
            components = get_components()
            
            assert components == (mock_components[0],) + mock_components[1:]
            assert isinstance(components[0], type(mock_components[0]))
            assert MockReasoningEngine.called_once_with(backend='auto')
            assert mock_logger.info.called_once_with(f"Model already loaded: test_model, using existing instance")
            assert _components_cache is not None

def test_get_components_error_handling(mock_logger):
    global _components_cache, _components_lock
    
    _components_cache = None
    _components_lock = MagicMock()
    
    with patch('neural_engine.api.routes.get_model_authority') as mock_get_authority:
        mock_get_authority.side_effect = ValueError("Invalid input")
        
        with pytest.raises(ValueError) as exc_info:
            get_components()
            
        assert str(exc_info.value) == "Invalid input"
        assert mock_logger.error.called_once_with("Failed to initialize components: Invalid input")

def test_get_components_async_behavior(mock_components, mock_model_authority, mock_logger):
    global _components_cache, _components_lock
    
    _components_cache = None
    _components_lock = MagicMock()
    
    with patch('neural_engine.api.routes.get_model_authority', return_value=mock_model_authority) as mock_get_authority:
        async def test_async_function():
            components = await get_components()
            assert components == mock_components
            assert isinstance(components[0], type(mock_components[0]))
            assert mock_logger.info.called_once_with("🔧 Initializing neural components (first request)...")
            assert _components_cache is not None
        
        import asyncio
        asyncio.run(test_async_function())