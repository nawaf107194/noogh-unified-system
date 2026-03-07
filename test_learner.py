import asyncio
from agents.autonomous_learner_agent import NooghAutonomousLearner

async def test():
    print("Testing Learner Agent manually to check output...")
    try:
        learner = NooghAutonomousLearner()
        # Initialize and try to run a basic knowledge scan
        summary = await learner.run_once()
        print(f"Learner Result: {summary}")
    except Exception as e:
        print(f"Learner Error: {e}")

asyncio.run(test())
