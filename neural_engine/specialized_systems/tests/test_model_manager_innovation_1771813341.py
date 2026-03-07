import pytest

from neural_engine.specialized_systems.model_manager import ModelManager

class TestModelManager:

    @pytest.fixture
    def model_manager(self):
        return ModelManager()

    def test_list_models_happy_path(self, model_manager):
        # Arrange
        expected_models = ['model1', 'model2', 'model3']
        for model in expected_models:
            model_manager.register_model(model)

        # Act
        result = model_manager.list_models()

        # Assert
        assert result == expected_models

    def test_list_models_empty(self, model_manager):
        # Arrange and Act
        result = model_manager.list_models()

        # Assert
        assert result == []

    def test_list_models_none(self, model_manager):
        # Arrange (not necessary for this function)
        
        # Act
        result = model_manager.list_models()

        # Assert
        assert result is not None

    def test_list_models_boundary(self, model_manager):
        # Arrange
        expected_model = 'model1'
        model_manager.register_model(expected_model)

        # Act
        result = model_manager.list_models()

        # Assert
        assert result == [expected_model]

    @pytest.mark.asyncio
    async def test_list_models_async(self, model_manager):
        # Arrange
        expected_models = ['model1', 'model2', 'model3']
        for model in expected_models:
            model_manager.register_model(model)

        # Act
        result = await model_manager.list_models()  # Assuming the method is async

        # Assert
        assert result == expected_models


if __name__ == '__main__':
    pytest.main(['-v', '-s', __file__])