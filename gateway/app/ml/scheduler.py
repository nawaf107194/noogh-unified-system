import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("scheduler")


class TrainingScheduler:
    """
    Manages a prioritized queue (Checklist) of topics for the Neural OS to learn.
    Allows user-directed learning to override or supplement passive dreaming.
    """

    def __init__(self, persistence_file: str = "learning_queue.json"):
        self.persistence_file = Path(persistence_file)
        self.queue: List[Dict[str, str]] = []  # List of {"topic": "...", "priority": "high/medium/low"}
        self._load_queue()
        logger.info(f"TrainingScheduler initialized. Items in queue: {len(self.queue)}")

    def add_topic(self, topic: str, priority: str = "high") -> int:
        """Add a topic to the learning checklist. Returns queue position."""
        item = {"topic": topic, "priority": priority}
        if priority == "high":
            self.queue.insert(0, item)  # FIFO for high priority? No, LIFO or insert at top.
        else:
            self.queue.append(item)

        self._save_queue()
        logger.info(f"Scheduler: Added '{topic}' to queue (Priority: {priority}). Total items: {len(self.queue)}")
        return len(self.queue)

    def get_next_topic(self) -> Optional[str]:
        """Pop the next topic from the queue."""
        if not self.queue:
            return None

        item = self.queue.pop(0)
        self._save_queue()
        logger.info(f"Scheduler: Popped '{item['topic']}' for training.")
        return item["topic"]

    def peek_queue(self) -> List[Dict[str, str]]:
        """View the current checklist without modifying it."""
        return self.queue

    def _save_queue(self):
        try:
            with open(self.persistence_file, "w") as f:
                json.dump(self.queue, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save learning queue: {e}")

    def _load_queue(self):
        if self.persistence_file.exists():
            try:
                with open(self.persistence_file, "r") as f:
                    self.queue = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load learning queue: {e}")
                self.queue = []
