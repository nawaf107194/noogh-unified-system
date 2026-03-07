import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
import torch

from neural_engine.image_processor import ImageProcessor

class TestImageProcessor:

    @pytest.fixture
    def image_processor(self):
        return ImageProcessor()

    @patch('neural_engine.image_processor.ImageProcessor._ensure_models_loaded')
    def test_generate_caption_happy_path(self, mock_ensure_models_loaded, image_processor):
        mock_blip_processor = MagicMock()
        mock_blip_model = MagicMock()
        generated_ids = [[1, 2, 3]]
        expected_caption = "Test caption"

        mock_blip_processor.decode.return_value = expected_caption
        mock_blip_model.generate.return_value = torch.tensor(generated_ids)

        with patch('neural_engine.image_processor.BlipProcessor', return_value=mock_blip_processor):
            with patch('neural_engine.image_processor.BlipModel', return_value=mock_blip_model):
                result = image_processor._generate_caption(Image.new("RGB", (1, 1)))

        assert result == expected_caption
        mock_ensure_models_loaded.assert_called_once()
        mock_blip_processor.decode.assert_called_once_with(generated_ids[0], skip_special_tokens=True)
        mock_blip_model.generate.assert_called_once()

    @patch('neural_engine.image_processor.ImageProcessor._ensure_models_loaded')
    def test_generate_caption_edge_case_empty_image(self, mock_ensure_models_loaded, image_processor):
        mock_blip_processor = MagicMock()
        mock_blip_model = MagicMock()

        with patch('neural_engine.image_processor.BlipProcessor', return_value=mock_blip_processor):
            with patch('neural_engine.image_processor.BlipModel', return_value=mock_blip_model):
                result = image_processor._generate_caption(Image.new("RGB", (0, 0)))

        assert result == "Caption generation failed"
        mock_ensure_models_loaded.assert_called_once()

    @patch('neural_engine.image_processor.ImageProcessor._ensure_models_loaded')
    def test_generate_caption_edge_case_none_image(self, mock_ensure_models_loaded, image_processor):
        with patch('neural_engine.image_processor.BlipProcessor'):
            with patch('neural_engine.image_processor.BlipModel'):
                result = image_processor._generate_caption(None)

        assert result == "Caption generation failed"
        mock_ensure_models_loaded.assert_called_once()

    def test_generate_caption_error_case_invalid_input(self, image_processor):
        with pytest.raises(TypeError):
            image_processor._generate_caption("not an image")