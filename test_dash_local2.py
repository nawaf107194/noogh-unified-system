import asyncio
import os
from dotenv import load_dotenv

load_dotenv('.env')
os.environ['NOOGH_INTERNAL_TOKEN'] = '107194'

from fastapi import Request
from gateway.app.api import dashboard
dashboard.NOOGH_INTERNAL_TOKEN = '107194'

from gateway.app.api.dashboard import chat_proxy

class FakeRequest:
    def __init__(self, json_body):
        self._json_body = json_body
        self.headers = {"x-forwarded-for": "127.0.0.1"}
        from unittest.mock import Mock
        self.client = Mock()
        self.client.host = "127.0.0.1"
        
    async def json(self):
        return self._json_body

async def test():
    req = FakeRequest({"message": "سعر البيتكوين سيهبط"})
    try:
        res = await chat_proxy(req, user={"role": "admin"})
        if hasattr(res, 'body'):
            print(res.body.decode('utf-8'))
        else:
            print(res)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test())
