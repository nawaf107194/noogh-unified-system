from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable

@dataclass
class State:
    data: Dict[str, Any] = field(default_factory=dict)
    observers: List[Callable[[dict], None]] = field(default_factory=list)

class StateManager:
    def __init__(self):
        self._state = State()
        
    def get_state(self, key: str) -> Optional[Any]:
        return self._state.data.get(key)
    
    def set_state(self, key: str, value: Any) -> None:
        old_value = self._state.data.get(key)
        self._state.data[key] = value
        if old_value != value:
            self._notify_observers(key, old_value, value)
            
    def subscribe(self, key: str, callback: Callable[[dict], None]) -> None:
        self._state.observers.append((key, callback))
        
    def _notify_observers(self, key: str, old_value: Any, new_value: Any) -> None:
        for observer in self._state.observers:
            if observer[0] == key:
                observer[1]({"key": key, "old": old_value, "new": new_value})
                
    @staticmethod
    def from_config(config_path: str) -> 'StateManager':
        # Integrate with DataRouter or other real DB tools
        return StateManager()