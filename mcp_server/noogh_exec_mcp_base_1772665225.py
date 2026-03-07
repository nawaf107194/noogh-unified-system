from abc import ABC, abstractmethod

class ExecutionStrategy(ABC):
    """Base interface for all execution strategies"""
    
    @abstractmethod
    def execute(self, task: dict) -> dict:
        """Execute the given task"""
        pass
    
    @abstractmethod
    def validate(self, task: dict) -> bool:
        """Validate the task before execution"""
        pass
    
    @abstractmethod
    def get_metrics(self) -> dict:
        """Return performance metrics for this strategy"""
        pass

class BaseMCPExecutor(ABC):
    """Base class for MCP executors"""

    def __init__(self, strategy: ExecutionStrategy):
        self.strategy = strategy
        self.task_queue = []
        self.results = []

    def set_strategy(self, strategy: ExecutionStrategy):
        """Set the execution strategy"""
        self.strategy = strategy

    def execute_task(self, task: dict) -> dict:
        """Execute a single task"""
        if not self.strategy.validate(task):
            raise ValueError("Invalid task")
        return self.strategy.execute(task)

    def execute_batch(self, tasks: list) -> list:
        """Execute multiple tasks"""
        results = []
        for task in tasks:
            try:
                result = self.execute_task(task)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        return results