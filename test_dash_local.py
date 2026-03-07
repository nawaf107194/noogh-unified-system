import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        r = await client.post(
            'http://127.0.0.1:8001/api/dashboard/chat/proxy',
            json={'message': 'ادعاء البيتكوين سيرتفع'},
            headers={'X-API-Key': '107194'}
        )
        print(f"Status: {r.status_code}")
        print(f"Text: {r.text}")

asyncio.run(test())
