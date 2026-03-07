from typing import Dict, Any
from dataclasses import dataclass
from unified_core.system.data_router import DataRouter

@dataclass
class EmotionalState:
    success_streak: int = 0
    failure_streak: int = 0
    last_action: str = ""
    timestamp: str = ""

class EmotionalContextTracker:
    def __init__(self):
        self.data_router = DataRouter()
        self.current_state = EmotionalState()
        
    def track_emotional_state(self, action: str, success: bool) -> None:
        """Update emotional state based on recent action outcome"""
        if success:
            self.current_state.success_streak += 1
            self.current_state.failure_streak = 0
        else:
            self.current_state.failure_streak += 1
            self.current_state.success_streak = 0
            
        self.current_state.last_action = action
        self._persist_state()
        
    def get_emotional_bias(self) -> Dict[str, Any]:
        """Get current emotional bias state"""
        return {
            "success_confidence": self.current_state.success_streak,
            "failure_avoidance": self.current_state.failure_streak,
            "last_action": self.current_state.last_action
        }
        
    def reset_emotional_state(self) -> None:
        """Reset emotional state counters"""
        self.current_state = EmotionalState()
        self._persist_state()
        
    def _persist_state(self) -> None:
        """Store current state using DataRouter"""
        state_data = {
            "success_streak": self.current_state.success_streak,
            "failure_streak": self.current_state.failure_streak,
            "last_action": self.current_state.last_action
        }
        self.data_router.store_data("emotional_state", state_data)
        
    def load_previous_state(self) -> None:
        """Load historical emotional state"""
        state_data = self.data_router.retrieve_data("emotional_state")
        if state_data:
            self.current_state = EmotionalState(
                success_streak=state_data.get("success_streak", 0),
                failure_streak=state_data.get("failure_streak", 0),
                last_action=state_data.get("last_action", "")
            )