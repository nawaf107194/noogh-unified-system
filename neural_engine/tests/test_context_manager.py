import pytest
from datetime import datetime
from typing import Dict, Any

class ContextManager:
    def __init__(self, user_intent: str, entities: Dict[str, Any], parameters: Dict[str, Any], timestamp: datetime):
        self.user_intent = user_intent
        self.entities = entities
        self.parameters = parameters
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_intent": self.user_intent,
            "entities": self.entities,
            "parameters": self.parameters,
            "timestamp": self.timestamp.isoformat(),
        }

@pytest.fixture
def context_manager_instance():
    return ContextManager(
        user_intent="book_flight",
        entities={"origin": "New York", "destination": "Los Angeles"},
        parameters={"date": "2023-05-01", "budget": 500},
        timestamp=datetime.now()
    )

def test_to_dict_happy_path(context_manager_instance):
    result = context_manager_instance.to_dict()
    assert isinstance(result, dict)
    assert "user_intent" in result
    assert "entities" in result
    assert "parameters" in result
    assert "timestamp" in result
    assert result["user_intent"] == "book_flight"
    assert result["entities"] == {"origin": "New York", "destination": "Los Angeles"}
    assert result["parameters"] == {"date": "2023-05-01", "budget": 500}
    assert isinstance(result["timestamp"], str)

def test_to_dict_empty_values():
    empty_cm = ContextManager(
        user_intent="",
        entities={},
        parameters={},
        timestamp=datetime.now()
    )
    result = empty_cm.to_dict()
    assert result["user_intent"] == ""
    assert result["entities"] == {}
    assert result["parameters"] == {}

def test_to_dict_none_values():
    none_cm = ContextManager(
        user_intent=None,
        entities=None,
        parameters=None,
        timestamp=datetime.now()
    )
    result = none_cm.to_dict()
    assert result["user_intent"] is None
    assert result["entities"] is None
    assert result["parameters"] is None

def test_to_dict_invalid_timestamp():
    with pytest.raises(AttributeError):
        invalid_cm = ContextManager(
            user_intent="book_flight",
            entities={"origin": "New York", "destination": "Los Angeles"},
            parameters={"date": "2023-05-01", "budget": 500},
            timestamp=None  # This should raise an AttributeError when calling isoformat()
        )
        invalid_cm.to_dict()

# Since the method does not involve async operations, there's no need to test for async behavior.