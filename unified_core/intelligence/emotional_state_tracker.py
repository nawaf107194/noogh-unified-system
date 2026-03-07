from typing import Dict, Any
from unified_core.memory.memory_store import MemoryStore

class EmotionalStateTracker:
    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store
        self.state: Dict[str, Any] = {
            'confidence': 0.5,  # 0-1 scale
            'success_streak': 0,
            'failure_streak': 0,
            'contextual_sentiment': 'neutral'
        }
        
    def _get_recent_activity(self, limit: int = 10):
        """Fetch recent activity logs from memory"""
        return self.memory_store.query(
            table='activity_logs',
            columns=['outcome', 'action', 'timestamp'],
            order_by='timestamp DESC',
            limit=limit
        )
    
    def update_state(self):
        """Update emotional state based on recent activity"""
        recent_activity = self._get_recent_activity()
        
        # Calculate success/failure streaks
        successes = sum(1 for log in recent_activity if log['outcome'] == 'success')
        failures = len(recent_activity) - successes
        
        self.state['success_streak'] = successes
        self.state['failure_streak'] = failures
        
        # Update confidence level
        self.state['confidence'] = max(0.1, min(0.9, 
            self.state['confidence'] + (0.1 if successes > failures else -0.1)
        ))
        
        # Determine contextual sentiment
        if failures > successes:
            self.state['contextual_sentiment'] = 'pessimistic'
        elif successes > failures:
            self.state['contextual_sentiment'] = 'optimistic'
        else:
            self.state['contextual_sentiment'] = 'neutral'
            
    def get_state(self) -> Dict[str, Any]:
        """Return current emotional state"""
        return self.state.copy()