import pytest
from unittest.mock import patch
from pathlib import Path
from unified_core.core.spatial_specialist import SpatialSpecialist

@pytest.fixture
def spatial_specialist_instance(tmp_path):
    return SpatialSpecialist(str(tmp_path))

def test_happy_path(spatial_specialist_instance):
    assert isinstance(spatial_specialist_instance.root_path, Path)
    assert spatial_specialist_instance.root_path.is_absolute()
    assert spatial_specialist_instance.spatial_map == {}

@patch('unified_core.core.spatial_specialist.logger')
def test_happy_path_logging(mock_logger, spatial_specialist_instance):
    mock_logger.info.assert_called_once_with(f"SpatialSpecialist initialized for root: {spatial_specialist_instance.root_path}")

def test_empty_string():
    with pytest.raises(ValueError, match="The root path cannot be empty"):
        SpatialSpecialist("")

def test_none_input():
    with pytest.raises(TypeError, match="'NoneType' object is not iterable"):
        SpatialSpecialist(None)

def test_invalid_input():
    with pytest.raises(ValueError, match="The root path provided is not valid"):
        SpatialSpecialist(":invalid_path")

def test_nonexistent_directory(tmp_path):
    non_existent_dir = tmp_path / "nonexistent"
    with pytest.raises(FileNotFoundError, match=f"No such file or directory: '{non_existent_dir}'"):
        SpatialSpecialist(str(non_existent_dir))

def test_async_behavior_not_applicable():
    # Since there's no async operation in the __init__ method,
    # we can skip this test or just state it as a comment.
    pass