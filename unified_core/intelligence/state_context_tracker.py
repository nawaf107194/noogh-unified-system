from typing import Dict, Any
from unified_core.system.data_router import DataRouter
from unified_core.utilities.events import StateChangeEvent

class StateContextTracker:
    def __init__(self):
        self.router = DataRouter()
        self.state_history: Dict[str, Any] = {}
        self.current_state = "normal"
        
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Fetch relevant metrics from data sources."""
        metrics = self.router.query({
            'resource_usage': {'metric': 'gpu_usage'},
            'task_success_rate': {'window': '5m'},
            'error_rate': {'window': '10m'}
        })
        return metrics
        
    def update_state(self) -> None:
        """Evaluate current state and trigger state changes if needed."""
        metrics = self._get_system_metrics()
        
        # Simple state evaluation logic
        if metrics['error_rate'] > 0.2:
            new_state = "high_stress"
        elif metrics['task_success_rate'] < 0.3:
            new_state = "idle"
        elif metrics['resource_usage'] > 0.8:
            new_state = "resource_limited"
        else:
            new_state = "normal"
            
        if new_state != self.current_state:
            self._trigger_state_change(new_state)
            
    def _trigger_state_change(self, new_state: str) -> None:
        """Handle state transitions and notify listeners."""
        self.current_state = new_state
        StateChangeEvent(state=new_state).publish()
        
    def get_current_state(self) -> str:
        """Return the current operational state."""
        return self.current_state
        
if __name__ == '__main__':
    tracker = StateContextTracker()
    tracker.update_state()
    print(f"Current state: {tracker.get_current_state()}")