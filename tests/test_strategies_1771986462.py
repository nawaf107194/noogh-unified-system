import pytest

class MockDatabase:
    def connect(self):
        return self

    def fetch_data(self):
        return "Data fetched from DB"

class TestRetrieveData:

    # Happy path test
    @pytest.mark.asyncio
    async def test_retrieve_data_happy_path(self, monkeypatch):
        db = MockDatabase()
        
        class RealStrategy:
            def __init__(self):
                self.db = db

            async def retrieve_data(self):
                return await db.fetch_data()

        real_strategy = RealStrategy()
        result = await real_strategy.retrieve_data()
        assert result == "Data fetched from DB"

    # Edge case: None input
    @pytest.mark.asyncio
    async def test_retrieve_data_none_input(self, monkeypatch):
        class RealStrategy:
            async def retrieve_data(self):
                return None

        strategy = RealStrategy()
        result = await strategy.retrieve_data()
        assert result is None

    # Edge case: Empty input
    @pytest.mark.asyncio
    async def test_retrieve_data_empty_input(self, monkeypatch):
        class RealStrategy:
            async def retrieve_data(self):
                return ""

        strategy = RealStrategy()
        result = await strategy.retrieve_data()
        assert result == ""

    # Error case: Invalid inputs (None input)
    @pytest.mark.asyncio
    async def test_retrieve_data_invalid_input_none(self, monkeypatch):
        class RealStrategy:
            async def retrieve_data(self):
                raise ValueError("Invalid input")

        with pytest.raises(ValueError) as exc_info:
            strategy = RealStrategy()
            await strategy.retrieve_data()

        assert str(exc_info.value) == "Invalid input"

# Example usage of monkeypatch
# @pytest.fixture(scope="module")
# def db_connection():
#     return MockDatabase()