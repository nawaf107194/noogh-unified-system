import asyncio
from typing import Callable, Any
from collections import deque

class AsyncTaskScheduler:
    def __init__(self):
        self.tasks = deque()
        self.loop = asyncio.get_event_loop()

    async def _execute_tasks(self):
        while True:
            if not self.tasks:
                await asyncio.sleep(0.1)  # Sleep briefly if no tasks are available
                continue
            task = self.tasks.popleft()
            await task()

    def add_task(self, task: Callable[..., Any], *args, **kwargs):
        """Add a task to the scheduler."""
        async_task = lambda: task(*args, **kwargs)
        self.tasks.append(async_task)
        if len(self.tasks) == 1:
            self.loop.create_task(self._execute_tasks())

    def run_until_complete(self):
        """Run the event loop until all tasks are completed."""
        self.loop.run_until_complete(self._execute_tasks())

    def stop(self):
        """Stop the scheduler and clear all pending tasks."""
        self.tasks.clear()
        self.loop.stop()

if __name__ == "__main__":
    async def sample_task(name):
        print(f"Executing {name}")
        await asyncio.sleep(1)
        print(f"{name} completed")

    scheduler = AsyncTaskScheduler()
    scheduler.add_task(sample_task, "Task 1")
    scheduler.add_task(sample_task, "Task 2")
    scheduler.run_until_complete()