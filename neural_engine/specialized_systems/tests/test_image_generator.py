import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def image_generator():
    img_gen = ImageGenerator()  # Assuming ImageGenerator is the class name
    img_gen.pipe = MagicMock()
    img_gen._initialized = True
    return img_gen

def test_unload_happy_path(image_generator):
    """Test the normal case where the pipe exists and is successfully unloaded."""
    image_generator.unload()
    assert image_generator.pipe is None
    assert not image_generator._initialized

@patch('torch.cuda.empty_cache')
def test_unload_calls_empty_cache(mock_empty_cache, image_generator):
    """Test that torch.cuda.empty_cache is called when unloading."""
    image_generator.unload()
    mock_empty_cache.assert_called_once()

def test_unload_with_none_pipe():
    """Test the edge case where the pipe is already None."""
    img_gen = ImageGenerator()  # Assuming ImageGenerator is the class name
    img_gen.pipe = None
    img_gen.unload()
    assert img_gen.pipe is None
    assert not img_gen._initialized

def test_unload_logger_info_called():
    """Test that the logger info is called when unloading."""
    img_gen = ImageGenerator()
    img_gen.pipe = MagicMock()
    with patch.object(img_gen.logger, 'info') as mock_info:
        img_gen.unload()
    mock_info.assert_called_once_with("ImageGenerator unloaded, GPU memory freed")

# Assuming error handling is part of the function's expected behavior,
# but since the provided function does not explicitly handle errors,
# we'll focus on coverage rather than raising exceptions.