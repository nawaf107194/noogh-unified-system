import pytest

from neural_engine.react_loop import get_react_loop, ReActLoop
from neural_engine.reasoning_engine import ReasoningEngine

@pytest.fixture(autouse=True)
def setup_teardown():
    yield
    global _instance
    _instance = None

def test_get_react_loop_happy_path():
    re_instance = ReActLoop()
    result = get_react_loop(re_instance)
    assert result == re_instance

def test_get_react_loop_no_reasoning_engine():
    result = get_react_loop()
    assert isinstance(result, ReActLoop)

def test_get_react_loop_reasoning_engine_none():
    global _instance
    _instance = None
    with pytest.raises(ImportError):
        get_react_loop()

def test_get_react_loop_reasoning_engine_failure():
    global _instance
    _instance = None
    from unittest.mock import patch
    with patch('neural_engine.reasoning_engine.ReasoningEngine') as mock_reasoning_engine:
        mock_reasoning_engine.side_effect = Exception("Test error")
        result = get_react_loop()
        assert isinstance(result, ReActLoop)
        assert result.reasoning_engine is None

def test_get_react_loop_async_behavior():
    async def create_reasoning_engine():
        return ReasoningEngine(backend="auto")

    global _instance
    _instance = None
    from asyncio import run
    reasoning_engine = run(create_reasoning_engine())
    result = get_react_loop(reasoning_engine)
    assert isinstance(result, ReActLoop)

def test_get_react_loop_instance_retention():
    re_instance_1 = ReActLoop()
    get_react_loop(re_instance_1)
    
    re_instance_2 = ReActLoop()
    get_react_loop()

    result = get_react_loop()
    assert result == re_instance_1