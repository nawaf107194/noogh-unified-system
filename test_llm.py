import asyncio
from dotenv import load_dotenv
load_dotenv('.env')

from unified_core.neural_bridge import NeuralEngineClient

async def test():
    client = NeuralEngineClient()
    print("Mode:", client.mode)
    res = await client.complete([{"role": "system", "content": "أجب باختصار"}, {"role": "user", "content": "لماذا تشرق الشمس؟"}], max_tokens=100)
    print("Completion:", res)

asyncio.run(test())
