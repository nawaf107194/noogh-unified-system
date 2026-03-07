import pytest
from unittest.mock import patch, MagicMock

class MockCLIPModel(MagicMock):
    pass

class MockBLIPForConditionalGeneration(MagicMock):
    pass

class MockCLIPProcessor(MagicMock):
    pass

class MockBLIPProcessor(MagicMock):
    pass

class MockLogger:
    @staticmethod
    def info(message):
        print(f"INFO: {message}")

    @staticmethod
    def error(message):
        print(f"ERROR: {message}")

@pytest.fixture
def image_processor():
    return ImageProcessor()

@patch("neural_engine.image_processor.CLIPModel", new=MockCLIPModel)
@patch("neural_engine.image_processor.CLIPProcessor", new=MockCLIPProcessor)
@patch("neural_engine.image_processor.BlipForConditionalGeneration", new=MockBLIPForConditionalGeneration)
@patch("neural_engine.image_processor.BlipProcessor", new=MockBLIPProcessor)
@patch("neural_engine.image_processor.logger", new=MockLogger())
def test_ensure_models_loaded_happy_path(image_processor):
    image_processor._initialized = False
    with patch.object(MockCLIPModel, "from_pretrained") as mock_clip_load:
        with patch.object(MockBLIPForConditionalGeneration, "from_pretrained") as mock_blip_load:
            mock_clip_load.return_value = MockCLIPModel()
            mock_blip_load.return_value = MockBLIPForConditionalGeneration()
            image_processor._ensure_models_loaded()
    assert image_processor.clip_model is not None
    assert image_processor.clip_processor is not None
    assert image_processor.blip_model is not None
    assert image_processor.blip_processor is not None
    assert image_processor._initialized is True

@patch("neural_engine.image_processor.CLIPModel", new=MockCLIPModel)
@patch("neural_engine.image_processor.CLIPProcessor", new=MockCLIPProcessor)
@patch("neural_engine.image_processor.BlipForConditionalGeneration", new=MockBLIPForConditionalGeneration)
@patch("neural_engine.image_processor.BlipProcessor", new=MockBLIPProcessor)
@patch("neural_engine.image_processor.logger", new=MockLogger())
def test_ensure_models_loaded_error_paths(image_processor):
    image_processor._initialized = False
    with patch.object(MockCLIPModel, "from_pretrained") as mock_clip_load:
        with patch.object(MockBLIPForConditionalGeneration, "from_pretrained") as mock_blip_load:
            mock_clip_load.side_effect = Exception("Mocked CLIP load error")
            mock_blip_load.return_value = MockBLIPForConditionalGeneration()
            image_processor._ensure_models_loaded()
    assert image_processor.clip_model is None
    assert image_processor.clip_processor is None
    assert image_processor.blip_model is not None
    assert image_processor.blip_processor is not None
    assert image_processor._initialized is True

    image_processor._initialized = False
    with patch.object(MockCLIPModel, "from_pretrained") as mock_clip_load:
        with patch.object(MockBLIPForConditionalGeneration, "from_pretrained") as mock_blip_load:
            mock_clip_load.return_value = MockCLIPModel()
            mock_blip_load.side_effect = Exception("Mocked BLIP load error")
            image_processor._ensure_models_loaded()
    assert image_processor.clip_model is not None
    assert image_processor.clip_processor is not None
    assert image_processor.blip_model is None
    assert image_processor.blip_processor is None
    assert image_processor._initialized is True

@patch("neural_engine.image_processor.CLIPModel", new=MockCLIPModel)
@patch("neural_engine.image_processor.CLIPProcessor", new=MockCLIPProcessor)
@patch("neural_engine.image_processor.BlipForConditionalGeneration", new=MockBLIPForConditionalGeneration)
@patch("neural_engine.image_processor.BlipProcessor", new=MockBLIPProcessor)
@patch("neural_engine.image_processor.logger", new=MockLogger())
def test_ensure_models_loaded_already_initialized(image_processor):
    image_processor._initialized = True
    with patch.object(MockCLIPModel, "from_pretrained") as mock_clip_load:
        with patch.object(MockBLIPForConditionalGeneration, "from_pretrained") as mock_blip_load:
            image_processor._ensure_models_loaded()
    assert image_processor.clip_model is None
    assert image_processor.clip_processor is None
    assert image_processor.blip_model is None
    assert image_processor.blip_processor is None
    assert image_processor._initialized is True

# Assuming `_ensure_models_loaded` does not involve async behavior, no need for additional tests here.