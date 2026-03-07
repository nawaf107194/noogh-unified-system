from abc import ABC, abstractmethod
from dataclasses import asdict

class StatePersistenceStrategy(ABC):
    """Interface for state persistence strategies"""
    
    @abstractmethod
    async def save_state(self, state) -> None:
        """Save the current state"""
        pass
    
    @abstractmethod
    async def load_state(self) -> dict:
        """Load the saved state"""
        pass

class DatabaseStateStrategy(StatePersistenceStrategy):
    """Database-backed state persistence"""
    
    def __init__(self, db_connection):
        self.db_connection = db_connection
        
    async def save_state(self, state) -> None:
        """Save state to database"""
        state_dict = asdict(state)
        await self.db_connection.execute(
            "INSERT INTO state (data) VALUES ($1) ON CONFLICT (id) DO UPDATE SET data = $1",
            state_dict
        )
        
    async def load_state(self) -> dict:
        """Load state from database"""
        result = await self.db_connection.fetchrow("SELECT data FROM state")
        return dict(result["data"]) if result else {}

class StateManager:
    def __init__(self, strategy: StatePersistenceStrategy):
        self.strategy = strategy
        self.current_state = {}
        
    async def save(self):
        await self.strategy.save_state(self.current_state)
        
    async def load(self):
        self.current_state = await self.strategy.load_state()