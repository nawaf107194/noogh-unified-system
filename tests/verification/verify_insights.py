import asyncio
import logging
from neural_engine.memory_consolidator import MemoryConsolidator

# Setup basic logging
logging.basicConfig(level=logging.ERROR)

async def verify():
    memory = MemoryConsolidator(base_dir="/home/noogh/projects/noogh_unified_system/data")
    
    print("Verifying Dream Insights...")
    
    # Try fetching by type
    insights = await memory.recall_by_type("dream_insight", n=50)
    
    if not insights:
        # Fallback search in content if type tagging failed for some reason
        recent = await memory.recall_recent(n=100)
        insights = [m for m in recent if "DREAM INSIGHT" in m.get("content", "")]
    
    print(f"Found {len(insights)} insights.")
    for idx, insight in enumerate(insights[:5]):
        print(f"Insight {idx+1}: {insight.get('content')} (Conf: {insight.get('metadata', {}).get('confidence')})")

if __name__ == "__main__":
    asyncio.run(verify())
