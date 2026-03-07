import pytest

class MockIntelligenceSystem:
    def __init__(self, support_levels=None, resistance_levels=None):
        self.support_levels = support_levels if support_levels is not None else []
        self.resistance_levels = resistance_levels if resistance_levels is not None else []

    def get_levels(self):
        """Returns the current support and resistance levels."""
        return self.support_levels, self.resistance_levels

@pytest.fixture
def intelligence_system():
    return MockIntelligenceSystem()

def test_get_levels_happy_path(intelligence_system):
    # Set up
    intelligence_system.support_levels = [10, 20, 30]
    intelligence_system.resistance_levels = [40, 50, 60]

    # Call the method
    result = intelligence_system.get_levels()

    # Assert the expected output
    assert result == ([10, 20, 30], [40, 50, 60])

def test_get_levels_empty(intelligence_system):
    # Set up
    intelligence_system.support_levels = []
    intelligence_system.resistance_levels = []

    # Call the method
    result = intelligence_system.get_levels()

    # Assert the expected output
    assert result == ([], [])

def test_get_levels_none_values(intelligence_system):
    # Set up
    intelligence_system.support_levels = None
    intelligence_system.resistance_levels = None

    # Call the method
    result = intelligence_system.get_levels()

    # Assert the expected output
    assert result == (None, None)

def test_get_levels_mixed_types(intelligence_system):
    # Set up
    intelligence_system.support_levels = [10, "20", 30.5]
    intelligence_system.resistance_levels = ["40", 50, None]

    # Call the method
    result = intelligence_system.get_levels()

    # Assert the expected output
    assert result == ([10, "20", 30.5], ["40", 50, None])

def test_get_levels_async_behavior(intelligence_system):
    # Set up
    async def mock_get_levels():
        return ([10, 20, 30], [40, 50, 60])
    
    intelligence_system.get_levels = mock_get_levels

    # Call the method
    result = await intelligence_system.get_levels()

    # Assert the expected output
    assert result == ([10, 20, 30], [40, 50, 60])