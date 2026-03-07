import pytest

class ExampleClass:
    def __init__(self, strategy):
        self._strategy = strategy

    def strategy(self):
        return self._strategy

@pytest.fixture
def example_class():
    return ExampleClass

def test_strategy_happy_path(example_class):
    mock_strategy = "test_strategy"
    obj = example_class(mock_strategy)
    assert obj.strategy() == mock_strategy

def test_strategy_edge_case_none(example_class):
    obj = example_class(None)
    assert obj.strategy() is None

def test_strategy_edge_case_empty_string(example_class):
    obj = example_class("")
    assert obj.strategy() == ""

def test_strategy_async_behavior():
    async def async_strategy():
        return "async_test_strategy"

    class AsyncExampleClass:
        def __init__(self, strategy):
            self._strategy = strategy

        async def strategy(self):
            return await self._strategy()

    obj = AsyncExampleClass(async_strategy)
    result = asyncio.run(obj.strategy())
    assert result == "async_test_strategy"