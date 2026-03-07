import asyncio
from typing import List, Dict, Callable

class TaskDependencyManager:
    def __init__(self):
        self.tasks = {}
        self.dependencies = {}

    def add_task(self, task_name: str, task_func: Callable, depends_on: List[str] = None):
        """Add a new task with its dependencies."""
        self.tasks[task_name] = task_func
        self.dependencies[task_name] = depends_on if depends_on else []

    async def execute_tasks(self):
        """Execute all tasks respecting their dependencies."""
        completed_tasks = set()

        async def execute_task(task_name):
            if task_name not in completed_tasks:
                await asyncio.gather(*(execute_task(dep) for dep in self.dependencies[task_name]))
                await self.tasks[task_name]()
                completed_tasks.add(task_name)

        await asyncio.gather(*[execute_task(task_name) for task_name in self.tasks.keys()])

# Example usage
async def task_a():
    print("Executing task A")

async def task_b():
    print("Executing task B")

async def task_c():
    print("Executing task C")

manager = TaskDependencyManager()
manager.add_task('task_a', task_a)
manager.add_task('task_b', task_b, ['task_a'])
manager.add_task('task_c', task_c, ['task_b'])

asyncio.run(manager.execute_tasks())