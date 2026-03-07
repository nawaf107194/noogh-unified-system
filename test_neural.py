import asyncio
from unified_core.neural_bridge import NeuralEngineClient

def test_sync():
    async def _run():
        client = NeuralEngineClient()
        messages = [{"role": "user", "content": "لماذا تشرق الشمس؟ أجب باختصار."}]
        res = await client.complete(messages, max_tokens=100)
        return res
        
    print(asyncio.run(_run()))

if __name__ == '__main__':
    test_sync()
