import pytest

from neural_engine.specialized_systems.model_manager import ModelManager, AIModelType, AIModel
from typing import Dict, Any, Optional

@pytest.fixture
def model_manager():
    return ModelManager()

@pytest.fixture
def valid_model():
    class MockModel:
        pass
    return MockModel()

def test_register_model_happy_path(model_manager, valid_model):
    name = "test_model"
    model_type = AIModelType.TRAINING
    metadata = {"description": "A test model"}
    
    result = model_manager.register_model(name, model_type, valid_model, metadata)
    
    assert isinstance(result, AIModel)
    assert result.name == name
    assert result.model_type == model_type
    assert result.model is valid_model
    assert result.metadata == metadata
    assert name in model_manager.models
    assert name in model_manager.model_by_type[model_type]

def test_register_model_empty_name(model_manager, valid_model):
    with pytest.raises(ValueError) as exc_info:
        model_manager.register_model("", AIModelType.TRAINING, valid_model)
    
    error_message = str(exc_info.value)
    assert "Model" in error_message
    assert "already registered" not in error_message

def test_register_model_none_name(model_manager, valid_model):
    with pytest.raises(ValueError) as exc_info:
        model_manager.register_model(None, AIModelType.TRAINING, valid_model)
    
    error_message = str(exc_info.value)
    assert "Model" in error_message
    assert "already registered" not in error_message

def test_register_model_invalid_model_type(model_manager, valid_model):
    class InvalidModelType:
        pass
    
    with pytest.raises(ValueError) as exc_info:
        model_manager.register_model("test_model", InvalidModelType(), valid_model)
    
    error_message = str(exc_info.value)
    assert "Invalid" in error_message

def test_register_model_existing_name(model_manager, valid_model):
    name = "existing_model"
    model_type = AIModelType.TRAINING
    metadata = {"description": "An existing model"}
    
    # Register the initial model
    initial_model = model_manager.register_model(name, model_type, valid_model, metadata)
    
    with pytest.raises(ValueError) as exc_info:
        model_manager.register_model(name, model_type, valid_model, metadata)
    
    error_message = str(exc_info.value)
    assert f"Model {name} already registered" in error_message

def test_register_model_no_metadata(model_manager, valid_model):
    name = "test_model"
    model_type = AIModelType.TRAINING
    
    result = model_manager.register_model(name, model_type, valid_model)
    
    assert isinstance(result, AIModel)
    assert result.name == name
    assert result.model_type == model_type
    assert result.model is valid_model
    assert result.metadata is None
    assert name in model_manager.models
    assert name in model_manager.model_by_type[model_type]