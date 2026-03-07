import pytest
from pathlib import Path
from unified_core.core.spatial_specialist import SpatialSpecialist

def test_spatial_specialist_happy_path():
    root_path = "/valid/path"
    specialist = SpatialSpecialist(root_path)
    assert isinstance(specialist, SpatialSpecialist)
    assert specialist.root_path == Path(root_path).resolve()
    assert specialist.spatial_map == {}
    assert logger.info.call_args_list == [call(f"SpatialSpecialist initialized for root: {Path(root_path).resolve()}")]

def test_spatial_specialist_edge_case_empty_root_path():
    root_path = ""
    specialist = SpatialSpecialist(root_path)
    assert isinstance(specialist, SpatialSpecialist)
    assert specialist.root_path == Path(".").resolve()
    assert specialist.spatial_map == {}
    assert logger.info.call_args_list == [call(f"SpatialSpecialist initialized for root: {Path(".").resolve()}")]

def test_spatial_specialist_edge_case_none_root_path():
    root_path = None
    specialist = SpatialSpecialist(root_path)
    assert isinstance(specialist, SpatialSpecialist)
    assert specialist.root_path == Path(".").resolve()
    assert specialist.spatial_map == {}
    assert logger.info.call_args_list == [call(f"SpatialSpecialist initialized for root: {Path(".").resolve()}")]

def test_spatial_specialist_error_case_invalid_root_path():
    root_path = 12345
    specialist = SpatialSpecialist(root_path)
    assert isinstance(specialist, SpatialSpecialist)
    assert specialist.root_path == Path(".").resolve()
    assert specialist.spatial_map == {}
    assert logger.info.call_args_list == [call(f"SpatialSpecialist initialized for root: {Path(".").resolve()}")]