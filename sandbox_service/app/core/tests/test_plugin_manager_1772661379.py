import pytest
from app.core.plugin_manager_1772661379 import decorator
from typing import Type

@pytest.fixture(autouse=True)
def reset_strategies():
    # Assuming _strategies is accessible or we need to mock it
    # This would need to be adjusted based on actual class structure
    cls = type('Cls', (), {'_strategies': {}})
    yield
    cls._strategies.clear()

class TestDecorator:
    @pytest.mark.parametrize("name,strategy,expected_result", [
        ("valid_strategy", type("ValidStrategy", (), {}), True),
        ("", type("EmptyStrategy", (), {}), False),
        (None, type("NoneStrategy", (), {}), False),
        ("invalid_strategy", "not_a_class", False),
    ])
    def test_decorator(self, name: str, strategy: Type, expected_result: bool):
        # Setup
        class SandboxStrategy:
            pass
        
        # Create a test strategy class
        test_strategy = type("TestStrategy", (SandboxStrategy,), {})
        
        # Test
        if isinstance(strategy, type):
            decorated = decorator(test_strategy)
            assert (name in decorator.cls._strategies) == expected_result
            if expected_result:
                assert decorated == test_strategy
        else:
            with pytest.raises(TypeError):
                decorator(strategy)