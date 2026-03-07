import pytest
from unified_core.agent_learning import get_learning_hub, AgentLearningHub

@pytest.fixture(scope="module")
def hub_instance():
    return AgentLearningHub()

def test_happy_path(hub_instance):
    global _hub_instance
    _hub_instance = None
    result = get_learning_hub()
    assert isinstance(result, AgentLearningHub)
    assert result is hub_instance

def test_edge_case_none_input():
    global _hub_instance
    _hub_instance = None
    result = get_learning_hub(None)
    assert isinstance(result, AgentLearningHub)

def test_edge_case_empty_input():
    global _hub_instance
    _hub_instance = None
    result = get_learning_hub('')
    assert isinstance(result, AgentLearningHub)

def test_async_behavior(hub_instance):
    import asyncio

    async def test_get_learning_hub():
        global _hub_instance
        _hub_instance = None
        result = await get_learning_hub()
        assert isinstance(result, AgentLearningHub)
        assert result is hub_instance

    asyncio.run(test_get_learning_hub())