"""
KPI Calculator for Autonomic System.
Calculates 8 core operational metrics from event stream.
"""

import time
from typing import Dict, List, Any, Optional
from collections import Counter
import statistics


def safe_div(numerator, denominator, default=None):
    """Safe division that returns default on zero division."""
    if denominator == 0 or denominator is None:
        return default
    return round(numerator / denominator, 4) if numerator is not None else default


class KPICalculator:
    """Calculates operational KPIs from autonomic events."""
    
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.last_cleanup = time.time()
        
    def add_event(self, event: Dict[str, Any]):
        """Add event to buffer for KPI calculation."""
        self.events.append({
            **event,
            'received_at': time.time()
        })
        
        # Cleanup old events (keep last 24 hours)
        if time.time() - self.last_cleanup > 300:  # Every 5 minutes
            self._cleanup_old_events()
    
    def _cleanup_old_events(self):
        """Remove events older than 24 hours."""
        cutoff = time.time() - 86400
        self.events = [e for e in self.events if e.get('received_at', 0) > cutoff]
        self.last_cleanup = time.time()
    
    def _get_events_in_window(self, window_seconds: int) -> List[Dict[str, Any]]:
        """Get events within specified time window."""
        cutoff = time.time() - window_seconds
        return [e for e in self.events if e.get('received_at', 0) > cutoff]
    
    def calculate_all(self, window_seconds: int = 3600) -> Dict[str, Any]:
        """Calculate all KPIs for given time window."""
        events = self._get_events_in_window(window_seconds)
        
        return {
            'window_seconds': window_seconds,
            'total_events': len(events),
            'timestamp': time.time(),
            'kpis': {
                'approval_rate': self._calc_approval_rate(events),
                'success_rate': self._calc_success_rate(events),
                'avg_confidence': self._calc_avg_confidence(events),
                'action_dominance': self._calc_action_dominance(events),
                'loop_stability': self._calc_loop_stability(events),
                'health_score': self._calc_health_score(events),
                'blocked_rate': self._calc_blocked_rate(events),
                'events_per_minute': self._calc_events_per_minute(events, window_seconds)
            }
        }
    
    def _calc_approval_rate(self, events: List[Dict]) -> Optional[float]:
        """Decision approval rate (%)."""
        decisions = [e for e in events if e.get('type') == 'decision']
        if not decisions:
            return None
        
        approved = sum(1 for d in decisions if d.get('payload', {}).get('approved', False))
        rate = safe_div(approved, len(decisions), 0)
        return round(rate * 100, 2) if rate is not None else 0.0
    
    def _calc_success_rate(self, events: List[Dict]) -> Optional[float]:
        """Execution success rate (%)."""
        executions = [e for e in events if e.get('type') == 'execution']
        if not executions:
            return None
        
        successful = sum(1 for e in executions if e.get('payload', {}).get('success', False))
        rate = safe_div(successful, len(executions), 0)
        return round(rate * 100, 2) if rate is not None else 0.0
    
    def _calc_avg_confidence(self, events: List[Dict]) -> Optional[float]:
        """Average decision confidence."""
        decisions = [e for e in events if e.get('type') == 'decision']
        confidences = [d.get('payload', {}).get('confidence', 0) for d in decisions]
        confidences = [c for c in confidences if c > 0]  # Filter zeros
        
        if not confidences:
            return None
        
        return round(statistics.mean(confidences), 3)
    
    def _calc_action_dominance(self, events: List[Dict]) -> Optional[Dict[str, Any]]:
        """Action dominance analysis."""
        decisions = [e for e in events if e.get('type') == 'decision']
        actions = [d.get('payload', {}).get('action', 'unknown') for d in decisions]
        
        if not actions:
            return None
        
        action_counts = Counter(actions)
        most_common_action, most_common_count = action_counts.most_common(1)[0]
        dominance_percent = round((most_common_count / len(actions)) * 100, 2)
        
        return {
            'dominance_percent': dominance_percent,
            'dominant_action': most_common_action,
            'action_count': most_common_count,
            'total_actions': len(actions),
            'top_5_actions': [
                {'action': action, 'count': count, 'percent': round((count/len(actions))*100, 1)}
                for action, count in action_counts.most_common(5)
            ]
        }
    
    def _calc_loop_stability(self, events: List[Dict]) -> Optional[float]:
        """Loop stability index (0-1)."""
        observations = [e for e in events if e.get('type') == 'observation']
        
        if len(observations) < 2:
            return None
        
        # Calculate intervals between observations
        timestamps = sorted([o.get('received_at', 0) for o in observations])
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        
        if not intervals:
            return None
        
        # Stability = 1 - (coefficient of variation)
        mean_interval = statistics.mean(intervals)
        if mean_interval == 0:
            return None
        
        std_dev = statistics.stdev(intervals) if len(intervals) > 1 else 0
        coeff_variation = std_dev / mean_interval
        stability = max(0, 1 - coeff_variation)
        
        return round(stability, 3)
    
    def _calc_health_score(self, events: List[Dict]) -> Optional[float]:
        """Overall health score based on observations."""
        observations = [e for e in events if e.get('type') == 'observation']
        
        if not observations:
            return None
        
        # Get latest observation health data
        latest = max(observations, key=lambda x: x.get('received_at', 0))
        payload = latest.get('payload', {})
        
        cpu = payload.get('cpu_percent', 0)
        memory = payload.get('memory_percent', 0)
        
        # Simple health scoring (inverse of resource usage)
        cpu_score = max(0, 100 - cpu)
        memory_score = max(0, 100 - memory)
        
        health_score = (cpu_score + memory_score) / 2
        return round(health_score, 2)
    
    def _calc_blocked_rate(self, events: List[Dict]) -> Optional[float]:
        """Blocked decisions rate (%)."""
        decisions = [e for e in events if e.get('type') == 'decision']
        if not decisions:
            return None
        
        blocked = sum(1 for d in decisions if not d.get('payload', {}).get('approved', False))
        return round((blocked / len(decisions)) * 100, 2)
    
    def _calc_events_per_minute(self, events: List[Dict], window_seconds: int) -> float:
        """Events per minute rate."""
        if window_seconds == 0:
            return 0.0
        
        window_minutes = window_seconds / 60
        return round(len(events) / window_minutes, 2)
    
    def get_trends(self, window_seconds: int = 86400, buckets: int = 24) -> Dict[str, Any]:
        """Get KPI trends over time (bucketed)."""
        events = self._get_events_in_window(window_seconds)
        
        if not events:
            return {'buckets': [], 'trends': {}}
        
        # Create time buckets
        bucket_size = window_seconds / buckets
        now = time.time()
        bucket_edges = [now - (i * bucket_size) for i in range(buckets, 0, -1)]
        
        trends = {kpi: [] for kpi in ['approval_rate', 'success_rate', 'avg_confidence']}
        timestamps = []
        
        for i, start_time in enumerate(bucket_edges):
            end_time = start_time + bucket_size if i < len(bucket_edges) - 1 else now
            bucket_events = [e for e in events if start_time <= e.get('received_at', 0) < end_time]
            
            timestamps.append(int(start_time))
            
            # Calculate KPIs for this bucket
            trends['approval_rate'].append(self._calc_approval_rate(bucket_events))
            trends['success_rate'].append(self._calc_success_rate(bucket_events))
            trends['avg_confidence'].append(self._calc_avg_confidence(bucket_events))
        
        return {
            'timestamps': timestamps,
            'trends': trends,
            'buckets': buckets
        }
    
    def get_recent_events(self, window_seconds: int = 300, limit: int = 500) -> List[Dict[str, Any]]:
        """Get recent events for decision graph."""
        cutoff = time.time() - window_seconds
        recent = [e for e in self.events if e.get('received_at', 0) > cutoff]
        return recent[-limit:] if len(recent) > limit else recent


# Global instance
_kpi_calculator = None

def get_kpi_calculator() -> KPICalculator:
    """Get global KPI calculator instance."""
    global _kpi_calculator
    if _kpi_calculator is None:
        _kpi_calculator = KPICalculator()
    return _kpi_calculator
