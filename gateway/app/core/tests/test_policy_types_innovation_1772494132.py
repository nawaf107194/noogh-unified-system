import pytest
from dataclasses import asdict
from typing import Dict, Any

class PolicyTypes:
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def test_to_dict_happy_path():
    class TestPolicy(PolicyTypes):
        field1 = 123
        field2 = "example"
    
    policy_instance = TestPolicy()
    result = policy_instance.to_dict()
    assert isinstance(result, dict)
    assert result == {'field1': 123, 'field2': 'example'}

def test_to_dict_empty():
    class EmptyPolicy(PolicyTypes):
        pass
    
    policy_instance = EmptyPolicy()
    result = policy_instance.to_dict()
    assert isinstance(result, dict)
    assert result == {}

def test_to_dict_none():
    policy_instance = None
    with pytest.raises(AttributeError) as exc_info:
        policy_instance.to_dict()
    assert str(exc_info.value) == "'NoneType' object has no attribute 'to_dict'"

@pytest.mark.asyncio
async def test_to_dict_async_behavior():
    class AsyncPolicy(PolicyTypes):
        async def to_dict(self) -> Dict[str, Any]:
            return asdict(self)
    
    policy_instance = AsyncPolicy()
    result = await policy_instance.to_dict()
    assert isinstance(result, dict)
    assert result == {}