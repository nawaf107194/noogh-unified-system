import pytest

from neural_engine.specialized_systems.image_generator import ImageGenerator

@pytest.fixture
def image_generator():
    return ImageGenerator()

def test_get_status_happy_path(image_generator):
    """Test get_status with normal inputs."""
    expected_output = {
        "initialized": False,
        "model": None,
        "device": None,
        "output_dir": str(OUTPUT_DIR)
    }
    assert image_generator.get_status() == expected_output

def test_get_status_edge_case_initialized(image_generator):
    """Test get_status with initialized set to True."""
    image_generator._initialized = True
    expected_output = {
        "initialized": True,
        "model": None,
        "device": None,
        "output_dir": str(OUTPUT_DIR)
    }
    assert image_generator.get_status() == expected_output

def test_get_status_edge_case_model(image_generator):
    """Test get_status with a model set."""
    image_generator.model_id = "test_model"
    expected_output = {
        "initialized": False,
        "model": "test_model",
        "device": None,
        "output_dir": str(OUTPUT_DIR)
    }
    assert image_generator.get_status() == expected_output

def test_get_status_edge_case_device(image_generator):
    """Test get_status with a device set."""
    image_generator.device = "cpu"
    expected_output = {
        "initialized": False,
        "model": None,
        "device": "cpu",
        "output_dir": str(OUTPUT_DIR)
    }
    assert image_generator.get_status() == expected_output

def test_get_status_edge_case_output_dir(image_generator):
    """Test get_status with a different output directory."""
    new_output_dir = "/new/output/dir"
    setattr(image_generator, 'OUTPUT_DIR', new_output_dir)
    expected_output = {
        "initialized": False,
        "model": None,
        "device": None,
        "output_dir": str(new_output_dir)
    }
    assert image_generator.get_status() == expected_output