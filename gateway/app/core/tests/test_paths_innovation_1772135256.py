import pytest
from pathlib import Path
from gateway.app.core.paths import require_data_dir

def test_require_data_dir_happy_path():
    base_dir = '/home/noogh/data'
    result = require_data_dir(base_dir)
    assert result == Path(base_dir)
    assert result.is_dir()

def test_require_data_dir_empty_base_dir():
    with pytest.raises(RuntimeError, match="Data directory path is missing in SecretsManager"):
        require_data_dir('')

def test_require_data_dir_none_base_dir():
    with pytest.raises(RuntimeError, match="Data directory path is missing in SecretsManager"):
        require_data_dir(None)

def test_require_data_dir_invalid_base_dir():
    invalid_path = '/nonexistent/path/with/special/chars!@#'
    result = require_data_dir(invalid_path)
    assert result == Path(invalid_path)
    assert result.is_dir()