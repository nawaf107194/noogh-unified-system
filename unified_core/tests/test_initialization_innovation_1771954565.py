import pytest

from unified_core.initialization import InitializationSystem, ComponentState

class TestInitializationSystem:

    @pytest.fixture
    def initialization_system():
        return InitializationSystem()

    def test_happy_path(self, initialization_system):
        # Simulate some components and their states
        initialization_system._components = {
            'component1': ComponentState.INITIALIZED,
            'component2': ComponentState.NOT_INITIALIZED
        }
        
        status = initialization_system.get_status()
        expected_status = {
            'component1': 'INITIALIZED',
            'component2': 'NOT_INITIALIZED'
        }
        assert status == expected_status, f"Expected {expected_status}, but got {status}"

    def test_empty_components(self, initialization_system):
        # Simulate an empty components dictionary
        initialization_system._components = {}
        
        status = initialization_system.get_status()
        assert status == {}, "Expected an empty dictionary, but got something else"

    def test_async_behavior(self, initialization_system):
        # Simulate async behavior by setting up a lock and simulating a delay
        import asyncio

        async def simulate_delay():
            await asyncio.sleep(0.1)
        
        async def get_status_with_delay(system):
            await simulate_delay()
            return system.get_status()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            future = asyncio.run_coroutine_threadsafe(get_status_with_delay(initialization_system), loop)
            status = future.result(1)  # Wait for the result with a timeout
            assert status == {}
        finally:
            loop.close()

    def test_invalid_input(self, initialization_system):
        # Since there's no explicit input validation in the function,
        # this test is more about ensuring it doesn't crash with unexpected inputs
        invalid_inputs = [
            None,
            'not a dictionary',
            [1, 2, 3]
        ]

        for invalid_input in invalid_inputs:
            status = initialization_system.get_status(invalid_input)  # This should not raise an exception
            assert status is None, f"Expected None for input {invalid_input}, but got {status}"