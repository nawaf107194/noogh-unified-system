import pytest
from unittest.mock import patch
from pathlib import Path
from gateway.app.core.paths import require_data_dir

class TestRequireDataDir:

    @pytest.fixture
    def mock_path(self):
        with patch('pathlib.Path') as MockPath:
            instance = MockPath.return_value
            instance.exists.return_value = False
            yield instance

    def test_happy_path(self, tmpdir):
        # Normal input
        base_dir = tmpdir.mkdir("data")
        result = require_data_dir(str(base_dir))
        assert isinstance(result, Path)
        assert result.exists()

    def test_edge_case_empty_string(self):
        # Empty string input
        with pytest.raises(RuntimeError, match="Data directory path is missing in SecretsManager"):
            require_data_dir("")

    def test_edge_case_none(self):
        # None input
        with pytest.raises(RuntimeError, match="Data directory path is missing in SecretsManager"):
            require_data_dir(None)

    def test_error_case_invalid_input(self):
        # Invalid input (e.g., non-string)
        with pytest.raises(TypeError):
            require_data_dir(123)

    def test_async_behavior(self, event_loop):
        # Since the function is synchronous, we can still test it in an async context
        async def test():
            base_dir = "/tmp/data"
            result = await event_loop.run_in_executor(None, require_data_dir, base_dir)
            assert isinstance(result, Path)
            assert result.exists()
        event_loop.run_until_complete(test())