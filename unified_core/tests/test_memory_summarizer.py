import unittest
import asyncio
from unittest.mock import MagicMock
from unified_core.system.advanced_memory_summarizer import AdvancedMemorySummarizerAgent
from unified_core.neural_bridge import NeuralResponse

class TestMemorySummarizer(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_store = MagicMock()
        self.mock_neural = MagicMock()
        self.summarizer = AdvancedMemorySummarizerAgent(self.mock_store, self.mock_neural)

    async def test_summarize_batch_success(self):
        # Mock successful neural response
        mock_response = NeuralResponse(success=True, content="This is a summary.")
        self.mock_neural.process = MagicMock(return_value=asyncio.Future())
        self.mock_neural.process.return_value.set_result(mock_response)

        batch = [{"observation_id": "1", "content": "test"}]
        result = await self.summarizer.summarize_batch(batch)
        
        self.assertEqual(result, "This is a summary.")
        self.mock_neural.process.assert_called_once()

    async def test_run_summarization_cycle_not_enough_memories(self):
        # Mock store returns few memories
        self.mock_store.get_recent_observations = MagicMock(return_value=asyncio.Future())
        self.mock_store.get_recent_observations.return_value.set_result([{"id": 1}] * 5)
        
        await self.summarizer.run_summarization_cycle()
        
        self.mock_neural.process.assert_not_called()

if __name__ == "__main__":
    unittest.main()
