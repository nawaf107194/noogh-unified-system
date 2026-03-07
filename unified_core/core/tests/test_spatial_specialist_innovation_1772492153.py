import pytest
from pathlib import Path
from unified_core.core.spatial_specialist import SpatialSpecialist

def test_spatial_specialist_happy_path():
    root_path = "/some/valid/path"
    specialist = SpatialSpecialist(root_path)
    assert specialist.root_path == Path("/some/valid/path").resolve()
    assert specialist.spatial_map == {}
    assert "SpatialSpecialist initialized for root: /some/valid/path" in caplog.text

def test_spatial_specialist_empty_string():
    root_path = ""
    specialist = SpatialSpecialist(root_path)
    assert specialist.root_path == Path("").resolve()  # This will be an absolute path, typically '/'
    assert specialist.spatial_map == {}
    assert "SpatialSpecialist initialized for root: /" in caplog.text  # or the actual resolved path

def test_spatial_specialist_none():
    with pytest.raises(TypeError):
        specialist = SpatialSpecialist(None)

def test_spatial_specialist_invalid_path(capsys):
    root_path = "/this/path/does/not/exist"
    specialist = SpatialSpecialist(root_path)
    assert specialist.root_path == Path("/this/path/does/not/exist").resolve()
    assert specialist.spatial_map == {}
    assert "SpatialSpecialist initialized for root: /this/path/does/not/exist" in caplog.text
    captured_output = capsys.readouterr()
    assert captured_output.err != ""