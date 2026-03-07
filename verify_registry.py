import asyncio
import logging
from unified_core.tool_registry import get_unified_registry

logging.basicConfig(level=logging.INFO)

async def check():
    reg = get_unified_registry()
    tools = reg.list_tools()
    print("Total tools:", len(tools))
    print("Does proc.run exist?", "proc.run" in tools)
    print("All tools:", tools)
    
if __name__ == "__main__":
    asyncio.run(check())
