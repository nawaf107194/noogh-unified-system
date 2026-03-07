import pytest

from neural_engine.context_manager import ContextManager, Action, Result, Metadata

@pytest.fixture
def context_manager():
    return ContextManager(
        action=Action.PARSE,
        result=Result.SUCCESS,
        success=True,
        timestamp=datetime.now(),
        metadata={"key": "value"}
    )

def test_to_dict_happy_path(context_manager):
    result = context_manager.to_dict()
    assert result["action"] == Action.PARSE
    assert result["result"] == str(Result.SUCCESS)
    assert result["success"] is True
    assert isinstance(result["timestamp"], str)
    assert result["metadata"] == {"key": "value"}

def test_to_dict_edge_cases():
    cm = ContextManager(
        action=None,
        result=None,
        success=None,
        timestamp=None,
        metadata={}
    )
    result = cm.to_dict()
    assert result["action"] is None
    assert result["result"] is None
    assert result["success"] is None
    assert result["timestamp"] is None
    assert result["metadata"] == {}

def test_to_dict_error_cases():
    with pytest.raises(TypeError):
        ContextManager(
            action=123,  # Invalid type for action
            result="INVALID",  # Invalid value for result
            success="TRUE",  # Invalid type for success
            timestamp="2020-01-01",  # Invalid type for timestamp
            metadata=None  # None is not allowed for metadata
        )

def test_to_dict_async_behavior():
    async def create_context_manager():
        return ContextManager(
            action=Action.PARSE,
            result=Result.SUCCESS,
            success=True,
            timestamp=datetime.now(),
            metadata={"key": "value"}
        )
    
    cm = asyncio.run(create_context_manager())
    result = cm.to_dict()
    assert result["action"] == Action.PARSE
    assert result["result"] == str(Result.SUCCESS)
    assert result["success"] is True
    assert isinstance(result["timestamp"], str)
    assert result["metadata"] == {"key": "value"}