import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        # why question
        r1 = await client.post(
            "http://127.0.0.1:8001/api/dashboard/chat/proxy",
            json={"message": "لماذا السماء زرقاء؟"}
        )
        print("Response 1 (ActiveQuestioner):")
        print(r1.json())
        print("-" * 40)
        
        # claim evaluate
        r2 = await client.post(
            "http://127.0.0.1:8001/api/dashboard/chat/proxy",
            json={"message": "الاقتصاد العالمي سينهار قريباً وهذا ادعاء أؤمن به"}
        )
        print("Response 2 (CriticalThinker):")
        print(r2.json())

asyncio.run(test())
