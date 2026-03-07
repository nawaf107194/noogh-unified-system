from abc import ABC, abstractmethod
import asyncio

class BaseAgent(ABC):
    def __init__(self):
        self._running = False
    
    @abstractmethod
    async def start(self):
        """Starts the agent's main loop."""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stops the agent's main loop."""
        pass
    
    @abstractmethod
    async def process(self, data):
        """Processes incoming data."""
        pass
    
    async def run(self):
        """Main run loop for the agent."""
        self._running = True
        while self._running:
            # Simulate processing some data
            await self.process(None)
            await asyncio.sleep(1)  # Simulate periodic check or delay
    
    def is_running(self):
        return self._running

# Example usage in one of the agents
class DependencyAuditorAgent(BaseAgent):
    async def start(self):
        print("Starting Dependency Auditor Agent")
        asyncio.create_task(self.run())
    
    async def stop(self):
        print("Stopping Dependency Auditor Agent")
        self._running = False
    
    async def process(self, data):
        print("Processing data in Dependency Auditor Agent")

# Usage example
async def main():
    agent = DependencyAuditorAgent()
    await agent.start()
    await asyncio.sleep(5)  # Let the agent run for 5 seconds
    await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())