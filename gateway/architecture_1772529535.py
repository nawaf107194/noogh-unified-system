import pytest
from websockets.client import connect
from websockets.exceptions import ConnectionClosed

class WebSocketTestBase:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.client = None
        
    async def connect_client(self):
        """Establish WebSocket connection"""
        try:
            self.client = await connect(self.endpoint)
        except ConnectionClosed:
            pytest.fail("Failed to connect to WebSocket endpoint")
            
    async def send_message(self, message):
        """Send message to WebSocket server"""
        if self.client is None:
            await self.connect_client()
            
        await self.client.send(message)
        return await self.client.recv()
        
    async def close_connection(self):
        """Close WebSocket connection"""
        if self.client is not None:
            await self.client.close()
            
    def __del__(self):
        """Ensure connection is closed"""
        import asyncio
        if self.client is not None:
            asyncio.run(self.close_connection())