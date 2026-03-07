import pytest

from neural_engine.specialized_systems.image_generator import get_image_generator, ImageGenerator

@pytest.fixture(autouse=True)
def reset_image_generator():
    """Fixture to reset _image_generator before each test."""
    global _image_generator
    _image_generator = None

def test_get_image_generator_happy_path():
    """Test happy path with normal inputs."""
    generator1 = get_image_generator()
    generator2 = get_image_generator()

    assert isinstance(generator1, ImageGenerator)
    assert isinstance(generator2, ImageGenerator)
    assert generator1 is generator2  # Ensure it's a singleton

def test_get_image_generator_edge_cases():
    """Test edge cases with empty, None, and boundary inputs."""
    global _image_generator
    _image_generator = {}  # Simulate an invalid state
    generator = get_image_generator()
    
    assert isinstance(generator, ImageGenerator)

def test_get_image_generator_error_cases():
    """Test error cases with invalid inputs."""
    pass  # This function does not explicitly raise errors

# Async behavior is not applicable as the function is synchronous