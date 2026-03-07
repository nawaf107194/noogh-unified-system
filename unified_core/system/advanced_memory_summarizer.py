import asyncio
import logging
import time
import json
from typing import List, Dict, Any, Optional
from unified_core.core.memory_store import UnifiedMemoryStore
from unified_core.neural_bridge import NeuralEngineBridge, NeuralRequest

logger = logging.getLogger("unified_core.system.memory_summarizer")

class AdvancedMemorySummarizerAgent:
    """
    Advanced Memory Summarizer.
    Compresses episodic memories (observations, experiences) into semantic summaries.
    This prevents memory bloat and helps the system maintain long-term context efficiently.
    """
    def __init__(self, memory_store: Optional[UnifiedMemoryStore] = None, neural_bridge: Optional[NeuralEngineBridge] = None):
        self.memory_store = memory_store or UnifiedMemoryStore()
        self.neural_bridge = neural_bridge
        self.summarization_threshold_days = 7 # Archive memories older than 7 days
        self.batch_size = 20 # Number of memories to summarize in one go
        self._running = False

    async def start(self):
        """Starts the periodic summarization loop."""
        if self._running:
            return
        self._running = True
        logger.info("AdvancedMemorySummarizerAgent started.")
        asyncio.create_task(self._periodic_run())

    async def _periodic_run(self):
        """Runs the summarization cycle every 10 minutes (600s)."""
        while self._running:
            try:
                await self.run_summarization_cycle()
            except Exception as e:
                logger.error(f"Error in AdvancedMemorySummarizerAgent loop: {e}")
            await asyncio.sleep(600)

    async def stop(self):
        self._running = False
        """
        Main entry point for the summarization process.
        Identifies old memories, Batches them, Summarizes, and Cleans up.
        """
        logger.info("Starting Advanced Memory Summarization cycle...")
        
        # 1. Fetch recent observations as a sample (in a real system, we'd filter by date)
        # For the prototype, we'll just take the oldest 50.
        observations = await self.memory_store.get_recent_observations(limit=100)
        if len(observations) < 10:
            logger.info("Not enough memories to summarize. Skipping cycle.")
            return

        # Simple grouping: batch of 20
        batches = [observations[i:i + self.batch_size] for i in range(0, len(observations), self.batch_size)]
        
        for i, batch in enumerate(batches):
            summary = await self.summarize_batch(batch)
            if summary:
                # 2. Store as a semantic belief
                belief_key = f"semantic_summary_{int(time.time())}_{i}"
                await self.memory_store.set_belief(
                    belief_key, 
                    {"content": summary, "type": "memory_summary", "source_count": len(batch)},
                    utility=0.8
                )
                logger.info(f"Stored semantic summary: {belief_key}")
                
                # 3. Cleanup (In a real system, we'd delete the specific IDs in the batch)
                # For now, we'll just log it as the cleanup logic depends on exact ID matches.
                logger.info(f"Summarized {len(batch)} episodic memories.")

    async def summarize_batch(self, batch: List[Dict[str, Any]]) -> Optional[str]:
        """
        Send a batch of memories to the Neural Engine for summarization.
        """
        batch_text = "\n".join([json.dumps(m) for m in batch])
        prompt = (
            "Summarize the following episodic memories into a concise semantic summary. "
            "Extract key patterns, successes, and failures. Ignore redundant details.\n\n"
            f"Memories:\n{batch_text}"
        )
        
        request = NeuralRequest(query=prompt, urgency=0.3, require_decision=False)
        try:
            if not self.neural_bridge:
                from unified_core.neural_bridge import get_neural_bridge
                self.neural_bridge = get_neural_bridge()
                
            response = await self.neural_bridge.think_with_authority(request)
            if response.success:
                return response.content
            else:
                logger.error(f"Neural Engine failed to summarize: {response.content}")
                return None
        except Exception as e:
            logger.error(f"Error during summarization call: {e}")
            return None

async def main():
    # Simple test execution
    store = UnifiedMemoryStore()
    from unified_core.neural_bridge import get_neural_bridge
    bridge = get_neural_bridge()
    summarizer = AdvancedMemorySummarizerAgent(store, bridge)
    await summarizer.run_summarization_cycle()

if __name__ == "__main__":
    asyncio.run(main())