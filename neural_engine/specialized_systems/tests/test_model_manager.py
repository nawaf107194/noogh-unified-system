import pytest
from datetime import datetime
from typing import Any, Dict, Optional
from neural_engine.specialized_systems.model_manager import AIModelType, ModelManager

class MockAIModelType:
    def __init__(self, value: str):
        self.value = value

    def __eq__(self, other):
        return self.value == other.value

# Test data
valid_model_type = MockAIModelType('CNN')
valid_model = 'some_model_instance'
valid_metadata = {'author': 'John Doe', 'version': '1.0'}

def test_init_happy_path():
    manager = ModelManager('model_name', valid_model_type, valid_model, valid_metadata)
    assert manager.name == 'model_name'
    assert manager.type == valid_model_type
    assert manager.model == valid_model
    assert manager.metadata == valid_metadata
    assert manager.usage_count == 0
    assert manager.total_inference_time == 0.0
    assert isinstance(manager.created_at, datetime)

def test_init_with_empty_name():
    with pytest.raises(ValueError):
        ModelManager('', valid_model_type, valid_model)

def test_init_with_none_name():
    with pytest.raises(ValueError):
        ModelManager(None, valid_model_type, valid_model)

def test_init_with_invalid_model_type():
    with pytest.raises(TypeError):
        ModelManager('model_name', 'invalid_model_type', valid_model)

def test_init_with_none_model():
    with pytest.raises(ValueError):
        ModelManager('model_name', valid_model_type, None)

def test_init_with_none_metadata():
    manager = ModelManager('model_name', valid_model_type, valid_model, None)
    assert manager.metadata == {}

def test_init_with_empty_metadata():
    manager = ModelManager('model_name', valid_model_type, valid_model, {})
    assert manager.metadata == {}

def test_init_with_no_metadata():
    manager = ModelManager('model_name', valid_model_type, valid_model)
    assert manager.metadata == {}

def test_init_with_async_behavior():
    # Since there is no async behavior in the init method, this test is not applicable.
    pass