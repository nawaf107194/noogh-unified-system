import pytest
from typing import Optional

class MockScheduler:
    def __init__(self):
        self.queue = []

    def get_next_topic(self) -> Optional[str]:
        """Pop the next topic from the queue."""
        if not self.queue:
            return None

        item = self.queue.pop(0)
        self._save_queue()
        logger.info(f"Scheduler: Popped '{item['topic']}' for training.")
        return item["topic"]

    def _save_queue(self):
        pass  # Mock implementation

@pytest.fixture
def scheduler():
    return MockScheduler()

def test_happy_path(scheduler):
    scheduler.queue = [{"topic": "test_topic"}]
    result = scheduler.get_next_topic()
    assert result == "test_topic"

def test_edge_case_empty_queue(scheduler):
    result = scheduler.get_next_topic()
    assert result is None

def test_error_cases_not_applicable():
    pass  # There are no explicit error cases in the function