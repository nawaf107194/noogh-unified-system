import pytest
from neural_engine.specialized_systems.image_generator import ImageGenerator

@pytest.fixture
def image_generator():
    """Fixture to create an instance of ImageGenerator."""
    return ImageGenerator()

def test_get_status_happy_path(image_generator):
    """Test get_status with normal inputs."""
    status = image_generator.get_status()
    assert isinstance(status, dict)
    assert "initialized" in status
    assert "model" in status
    assert "device" in status
    assert "output_dir" in status
    assert isinstance(status["output_dir"], str)

def test_get_status_edge_case_none(image_generator):
    """Test get_status with None inputs."""
    image_generator._initialized = None
    image_generator.model_id = None
    image_generator.device = None
    status = image_generator.get_status()
    assert "initialized" in status and status["initialized"] is None
    assert "model" in status and status["model"] is None
    assert "device" in status and status["device"] is None
    assert "output_dir" in status and isinstance(status["output_dir"], str)

def test_get_status_edge_case_empty(image_generator):
    """Test get_status with empty string inputs."""
    image_generator._initialized = False
    image_generator.model_id = ""
    image_generator.device = ""
    status = image_generator.get_status()
    assert "initialized" in status and status["initialized"] is False
    assert "model" in status and status["model"] == ""
    assert "device" in status and status["device"] == ""
    assert "output_dir" in status and isinstance(status["output_dir"], str)

def test_get_status_edge_case_boundary(image_generator):
    """Test get_status with boundary conditions."""
    image_generator._initialized = True
    image_generator.model_id = "model123"
    image_generator.device = "cuda:0"
    status = image_generator.get_status()
    assert "initialized" in status and status["initialized"] is True
    assert "model" in status and status["model"] == "model123"
    assert "device" in status and status["device"] == "cuda:0"
    assert "output_dir" in status and isinstance(status["output_dir"], str)