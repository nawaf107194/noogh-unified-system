import asyncio
import os
from unified_core.neural_bridge import NeuralEngineClient

async def test():
    client = NeuralEngineClient()
    os.environ['NOOGH_INTERNAL_TOKEN'] = '107194'
    res = await client.reason("لماذا تشرق الشمس؟")
    print("Reason output:", res)

asyncio.run(test())
