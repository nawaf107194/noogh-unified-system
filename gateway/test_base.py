import asyncio
import unittest

class AsyncTestBase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Common setup logic for all async tests
        self.loop = asyncio.get_event_loop()
        # Example initialization
        self.server = await self.start_test_server()

    async def asyncTearDown(self):
        # Common teardown logic for all async tests
        await self.stop_test_server()

    async def start_test_server(self):
        # Implement server startup logic
        pass

    async def stop_test_server(self):
        # Implement server shutdown logic
        pass

# Example usage in a specific test file
class TestSpecificCase(AsyncTestBase):
    async def test_example(self):
        # Specific test logic
        assert True  # Replace with actual test logic

# gateway/test_ws.py
class TestWebSocket(AsyncTestBase):
    async def test_websocket_connection(self):
        # Specific test logic for websocket connection
        assert True  # Replace with actual test logic

# gateway/test_ws_final.py
class TestFinalWebSocket(AsyncTestBase):
    async def test_final_websocket_connection(self):
        # Specific test logic for final websocket connection
        assert True  # Replace with actual test logic

# gateway/test_ws_8001.py
class TestWebSocket8001(AsyncTestBase):
    async def test_websocket_8001(self):
        # Specific test logic for websocket on port 8001
        assert True  # Replace with actual test logic

# gateway/test_ws_2.py
class TestWebSocket2(AsyncTestBase):
    async def test_websocket_2(self):
        # Specific test logic for another websocket scenario
        assert True  # Replace with actual test logic

# gateway/test_ws_light.py
class TestLightWebSocket(AsyncTestBase):
    async def test_light_websocket(self):
        # Specific test logic for light websocket scenario
        assert True  # Replace with actual test logic