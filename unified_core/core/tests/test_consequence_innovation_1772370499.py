import pytest

from unified_core.core.consequence import Consequence

class MockConstraint:
    def __init__(self, pattern, constraint_type):
        self.pattern = pattern
        self.constraint_type = constraint_type

@pytest.fixture
def consequence():
    return Consequence()

def test_get_blocked_patterns_happy_path(consequence):
    # Arrange
    constraint1 = MockConstraint("pattern1", "block")
    constraint2 = MockConstraint("pattern2", "allow")
    consequence._constraints = {"c1": constraint1, "c2": constraint2}
    
    # Act
    result = consequence.get_blocked_patterns()
    
    # Assert
    assert result == ["pattern1"]

def test_get_blocked_patterns_empty_dict(consequence):
    # Arrange
    consequence._constraints = {}
    
    # Act
    result = consequence.get_blocked_patterns()
    
    # Assert
    assert result == []

def test_get_blocked_patterns_none_value(consequence):
    # Arrange
    consequence._constraints = None
    
    # Act
    result = consequence.get_blocked_patterns()
    
    # Assert
    assert result == []

def test_get_blocked_patterns_no_block_constraints(consequence):
    # Arrange
    constraint1 = MockConstraint("pattern1", "allow")
    constraint2 = MockConstraint("pattern2", "allow")
    consequence._constraints = {"c1": constraint1, "c2": constraint2}
    
    # Act
    result = consequence.get_blocked_patterns()
    
    # Assert
    assert result == []