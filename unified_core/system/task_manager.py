# unified_core/system/task_manager.py

from concurrent.futures import ThreadPoolExecutor
import logging
from typing import List, Callable

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self, max_workers: int):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit_task(self, task: Callable, *args, **kwargs) -> None:
        future = self.executor.submit(task, *args, **kwargs)
        future.add_done_callback(self._handle_completion)

    def _handle_completion(self, future):
        try:
            result = future.result()
            logger.info(f"Task completed successfully with result: {result}")
        except Exception as e:
            logger.error(f"Task failed with exception: {e}")

    def shutdown(self) -> None:
        self.executor.shutdown(wait=True)

# Example usage
if __name__ == '__main__':
    def sample_task(delay):
        import time
        time.sleep(delay)
        return f"Completed after {delay} seconds"

    task_manager = TaskManager(max_workers=5)
    for i in range(10):
        task_manager.submit_task(sample_task, delay=i)

    task_manager.shutdown()