import pytest

def sample_function():
    return "Success"

@handle_errors
def error_prone_function():
    raise ValueError("An error occurred")

@pytest.mark.asyncio
async def async_error_prone_function():
    raise asyncio.CancelledError("Async error occurred")

class TestHandleErrors:
    def test_happy_path(self):
        result = sample_function()
        assert result == "Success"

    def test_edge_case_none(self, monkeypatch):
        with pytest.raises(Exception) as exc_info:
            handle_errors(None)
        assert str(exc_info.value) == "Wrapped function is None"

    def test_error_case_explicitly_raised(self):
        with pytest.raises(ValueError):
            error_prone_function()

    async def test_async_behavior_explicitly_canceled(self, monkeypatch):
        with pytest.raises(asyncio.CancelledError):
            await async_error_prone_function()