import pytest
from pathlib import Path
from unittest.mock import patch

from gateway.app.core.paths import require_data_dir

class TestRequireDataDir:

    @pytest.fixture
    def mock_mkdir(self):
        with patch.object(Path, 'mkdir') as mock:
            yield mock

    def test_happy_path(self, tmp_path, mock_mkdir):
        # Test normal input
        base_dir = str(tmp_path / "data")
        result = require_data_dir(base_dir)
        assert result == Path(base_dir)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_empty_string_input(self):
        # Test edge case with empty string
        with pytest.raises(RuntimeError, match="Data directory path is missing in SecretsManager"):
            require_data_dir("")

    def test_none_input(self):
        # Test edge case with None
        with pytest.raises(RuntimeError, match="Data directory path is missing in SecretsManager"):
            require_data_dir(None)

    def test_invalid_input_type(self):
        # Test error case with invalid type
        with pytest.raises(TypeError):
            require_data_dir(123)  # Passing an integer instead of a string

    def test_directory_already_exists(self, tmp_path, mock_mkdir):
        # Test happy path where directory already exists
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        result = require_data_dir(str(existing_dir))
        assert result == existing_dir
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_async_behavior_not_applicable(self):
        # Since the function does not involve async operations, no async tests are needed
        pass