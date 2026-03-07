import pytest
from neural_engine.specialized_systems.model_manager import ModelManager

@pytest.fixture
def model_manager():
    return ModelManager()

def test_unregister_model_happy_path(model_manager):
    # Arrange
    model_name = "test_model"
    model_type = "test_type"
    model_manager.models[model_name] = {"type": model_type}
    model_manager.model_by_type[model_type] = [model_name]

    # Act
    result = model_manager.unregister_model(model_name)

    # Assert
    assert result is None
    assert model_name not in model_manager.models
    assert model_name not in model_manager.model_by_type[model_type]
    logger.info.assert_called_once_with("Unregistered model: test_model")

def test_unregister_model_empty_input(model_manager):
    # Arrange

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        model_manager.unregister_model("")
    
    assert "Model '' not found" in str(exc_info.value)

def test_unregister_model_none_input(model_manager):
    # Arrange

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        model_manager.unregister_model(None)
    
    assert "Model 'None' not found" in str(exc_info.value)

def test_unregister_model_non_existent_model(model_manager):
    # Arrange
    model_name = "nonexistent_model"

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        model_manager.unregister_model(model_name)
    
    assert f"Model {model_name} not found" in str(exc_info.value)