import pytest
from pathlib import Path
from gateway.app.core.paths import require_data_dir

def test_require_data_dir_happy_path():
    base_dir = "/tmp/test_data"
    path = require_data_dir(base_dir)
    assert isinstance(path, Path)
    assert path.exists()
    # Clean up
    path.rmdir()

def test_require_data_dir_empty_base_dir():
    with pytest.raises(RuntimeError):
        require_data_dir("")

def test_require_data_dir_none_base_dir():
    with pytest.raises(RuntimeError):
        require_data_dir(None)

def test_require_data_dir_existing_directory():
    base_dir = "/tmp/test_data_exists"
    Path(base_dir).mkdir(parents=True, exist_ok=False)
    path = require_data_dir(base_dir)
    assert isinstance(path, Path)
    assert path.exists()
    # Clean up
    path.rmdir()

# Async behavior not applicable as the function is synchronous