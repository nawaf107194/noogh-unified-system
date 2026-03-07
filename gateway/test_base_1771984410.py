# gateway/test_ws.py

from gateway.test_base import BaseTestCase

class TestWebsocket(BaseTestCase):
    async def test_connect(self):
        response = await self.client.get('/ws')
        self.assertEqual(response.status_code, 200)