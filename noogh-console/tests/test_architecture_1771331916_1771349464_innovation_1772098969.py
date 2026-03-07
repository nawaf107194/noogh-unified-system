import pytest

class MockStrategy:
    def get_gpu_info(self):
        return "Sample GPU Info"

def test_execute_strategy_happy_path(mocker):
    # Create an instance of the class with a mock strategy
    mock_strategy = MockStrategy()
    class_instance = YourClass(mock_strategy)  # Replace 'YourClass' with the actual class name

    # Call the execute_strategy method and capture the output
    captured_output = []
    with pytest.raises(SystemExit) as exc_info:
        with monkeypatch.context() as m:
            m.setattr('builtins.print', lambda x: captured_output.append(x))
            class_instance.execute_strategy()

    # Assert that the printed output is correct
    assert captured_output == ["Retrieved GPU Info: Sample GPU Info"]

def test_execute_strategy_edge_case(mocker):
    # Create an instance of the class with a mock strategy that returns None
    mock_strategy = MockStrategy()
    mock_strategy.get_gpu_info = lambda: None

    class_instance = YourClass(mock_strategy)  # Replace 'YourClass' with the actual class name

    # Call the execute_strategy method and capture the output
    captured_output = []
    with pytest.raises(SystemExit) as exc_info:
        with monkeypatch.context() as m:
            m.setattr('builtins.print', lambda x: captured_output.append(x))
            class_instance.execute_strategy()

    # Assert that no output is printed
    assert captured_output == []

def test_execute_strategy_async_behavior(mocker):
    # Create an instance of the class with a mock strategy that returns async results
    import asyncio

    async def async_gpu_info():
        return "Async GPU Info"

    mock_strategy = MockStrategy()
    mock_strategy.get_gpu_info = async_gpu_info

    class_instance = YourClass(mock_strategy)  # Replace 'YourClass' with the actual class name

    # Call the execute_strategy method and capture the output
    captured_output = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(class_instance.execute_strategy())
    finally:
        loop.close()

    # Assert that the printed output is correct
    assert captured_output == ["Retrieved GPU Info: Async GPU Info"]