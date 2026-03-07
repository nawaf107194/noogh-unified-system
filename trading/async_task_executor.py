import asyncio
from typing import Any, Dict, List, Optional

class AsyncTask:
    def __init__(self, name: str, coro: Any, params: Optional[Dict] = None):
        self.name = name
        self.coro = coro
        self.params = params or {}
        self.result = None
        self.exception = None

    async def execute(self):
        try:
            self.result = await self.coro(**self.params)
        except Exception as e:
            self.exception = e

class AsyncTaskExecutor:
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.tasks: List[AsyncTask] = []
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def add_task(self, name: str, coro: Any, params: Optional[Dict] = None):
        task = AsyncTask(name, coro, params)
        self.tasks.append(task)
        await self.semaphore.acquire()
        asyncio.create_task(self._execute_task(task))
        
    async def _execute_task(self, task: AsyncTask):
        await task.execute()
        self.semaphore.release()

    async def run_all(self):
        while self.tasks:
            await asyncio.gather(*[task.execute() for task in self.tasks])
            self.tasks.clear()

    def get_results(self) -> Dict[str, Any]:
        return {task.name: task.result for task in self.tasks if task.result is not None}

    def get_exceptions(self) -> Dict[str, Exception]:
        return {task.name: task.exception for task in self.tasks if task.exception is not None}