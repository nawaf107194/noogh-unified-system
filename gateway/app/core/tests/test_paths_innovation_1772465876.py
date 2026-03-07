import pytest
from pathlib import Path

def require_data_dir(base_dir: str) -> Path:
    """
    Ensure the data directory exists.
    base_dir must be provided from the validated SecretsManager.
    """
    if not base_dir:
        raise RuntimeError("Data directory path is missing in SecretsManager")
    path = Path(base_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

@pytest.mark.parametrize("base_dir, expected_result", [
    ("/tmp/data_dir", Path("/tmp/data_dir")),
])
def test_happy_path(base_dir, expected_result):
    result = require_data_dir(base_dir)
    assert result == expected_result
    assert result.is_dir()

@pytest.mark.parametrize("base_dir, expected_exception, expected_message", [
    (None, RuntimeError, "Data directory path is missing in SecretsManager"),
    ("", RuntimeError, "Data directory path is missing in SecretsManager"),
])
def test_edge_cases(base_dir, expected_exception, expected_message):
    with pytest.raises(expected_exception) as exc_info:
        require_data_dir(base_dir)
    assert str(exc_info.value) == expected_message