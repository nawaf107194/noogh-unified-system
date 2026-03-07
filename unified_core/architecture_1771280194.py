from typing import Any, Dict
import threading

class StateService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StateService, cls).__new__(cls)
                    cls._instance.state = {}
        return cls._instance

    def get_state(self, key: str) -> Any:
        """Retrieve state value by key."""
        return self.state.get(key)

    def set_state(self, key: str, value: Any) -> None:
        """Set state value by key."""
        self.state[key] = value

    def update_state(self, updates: Dict[str, Any]) -> None:
        """Update multiple state values at once."""
        self.state.update(updates)

# Example usage in other files
def some_function():
    state_service = StateService()
    state_service.set_state('user_id', '12345')
    user_id = state_service.get_state('user_id')
    print(f"User ID: {user_id}")

# In main.py or wherever appropriate
if __name__ == "__main__":
    # Initialize state service or use it directly
    state_service = StateService()
    state_service.set_state('initial_state', {'key': 'value'})