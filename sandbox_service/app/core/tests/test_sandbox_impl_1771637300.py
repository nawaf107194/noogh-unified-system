import pytest

class TestSandboxImpl:

    @pytest.mark.asyncio
    async def test_is_liquid_time_happy_path(self, sandbox_service):
        # Happy path: normal inputs
        result = await sandbox_service.is_liquid_time("2023-10-05T14:00:00Z")
        assert result is True  # Assuming the function returns True for valid liquid time

    @pytest.mark.asyncio
    async def test_is_liquid_time_empty_input(self, sandbox_service):
        # Edge case: empty input
        with pytest.raises(ValueError) as e:
            await sandbox_service.is_liquid_time("")
        assert str(e.value) == "Input cannot be empty"

    @pytest.mark.asyncio
    async def test_is_liquid_time_none_input(self, sandbox_service):
        # Edge case: None input
        with pytest.raises(ValueError) as e:
            await sandbox_service.is_liquid_time(None)
        assert str(e.value) == "Input cannot be None"

    @pytest.mark.asyncio
    async def test_is_liquid_time_boundary_input(self, sandbox_service):
        # Edge case: boundary input (e.g., just before midnight)
        result = await sandbox_service.is_liquid_time("2023-10-05T23:59:59Z")
        assert result is True  # Assuming the function returns True for valid liquid time

    @pytest.mark.asyncio
    async def test_is_liquid_time_invalid_format(self, sandbox_service):
        # Error case: invalid input format
        with pytest.raises(ValueError) as e:
            await sandbox_service.is_liquid_time("2023-10-05T14:00")
        assert str(e.value) == "Invalid time format"

    @pytest.mark.asyncio
    async def test_is_liquid_time_non_string_input(self, sandbox_service):
        # Error case: non-string input
        with pytest.raises(ValueError) as e:
            await sandbox_service.is_liquid_time(12345)
        assert str(e.value) == "Input must be a string"