import pytest
from unified_core.core.consequence import verify_constraints, Constraint, Action

class MockConstraint1(Constraint):
    def applies_to(self, proposed_action: Action) -> bool:
        return proposed_action.name == "action1"

class MockConstraint2(Constraint):
    def applies_to(self, proposed_action: Action) -> bool:
        return proposed_action.name == "action2"

@pytest.fixture
def consequence():
    return Consequence()

def test_verify_constraints_happy_path(consequence):
    proposed_action = Action(name="action1")
    constraint1 = MockConstraint1()
    constraint2 = MockConstraint2()
    consequence._constraints = {"constraint1": constraint1, "constraint2": constraint2}
    
    result = consequence.verify_constraints(proposed_action)
    
    assert len(result) == 1
    assert result[0] is constraint1

def test_verify_constraints_empty(consequence):
    proposed_action = Action(name="action1")
    consequence._constraints = {}
    
    result = consequence.verify_constraints(proposed_action)
    
    assert not result

def test_verify_constraints_none(consequence):
    proposed_action = None
    with pytest.raises(TypeError) as exc_info:
        consequence.verify_constraints(proposed_action)
    
    assert "Expected an instance of Action" in str(exc_info.value)

def test_verify_constraints_invalid_action(consequence):
    proposed_action = "not_an_action"
    with pytest.raises(TypeError) as exc_info:
        consequence.verify_constraints(proposed_action)
    
    assert "Expected an instance of Action" in str(exc_info.value)

class AsyncMockConstraint1(Constraint):
    async def applies_to(self, proposed_action: Action) -> bool:
        return proposed_action.name == "action1"

@pytest.mark.asyncio
async def test_verify_constraints_async(consequence):
    proposed_action = Action(name="action1")
    constraint1 = AsyncMockConstraint1()
    consequence._constraints = {"constraint1": constraint1}
    
    result = await consequence.verify_constraints(proposed_action)
    
    assert len(result) == 1
    assert result[0] is constraint1