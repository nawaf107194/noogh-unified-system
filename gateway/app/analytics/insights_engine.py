"""
Insights Engine for Autonomic System.
Detects anomalies, generates recommendations, provides intelligence.
"""

from typing import Dict, List, Any, Optional
from enum import Enum


class InsightSeverity(str, Enum):
    """Insight severity levels."""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    CAUTION = "caution"
    CRITICAL = "critical"


class Insight:
    """Single insight with severity and recommendation."""
    
    def __init__(self, rule_name: str, severity: InsightSeverity, 
                 message: str, explanation: str, recommendation: Optional[str] = None):
        self.rule_name = rule_name
        self.severity = severity
        self.message = message
        self.explanation = explanation
        self.recommendation = recommendation
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'rule': self.rule_name,
            'severity': self.severity.value,
            'message': self.message,
            'explanation': self.explanation,
            'recommendation': self.recommendation
        }


class InsightsEngine:
    """Analyzes KPIs and generates actionable insights."""
    
    def __init__(self, kpi_calculator):
        self.kpi_calc = kpi_calculator
    
    def analyze(self, window_seconds: int = 3600) -> List[Insight]:
        """Run all insight rules and return active insights."""
        kpis = self.kpi_calc.calculate_all(window_seconds)
        insights = []
        
        # Run all rules
        insights.extend(self._rule_over_blocking(kpis))
        insights.extend(self._rule_over_executing(kpis))
        insights.extend(self._rule_action_dominance(kpis))
        insights.extend(self._rule_execution_failures(kpis))
        insights.extend(self._rule_low_activity(kpis))
        insights.extend(self._rule_unstable_loop(kpis))
        insights.extend(self._rule_perfect_balance(kpis))
        insights.extend(self._rule_low_confidence(kpis))
        
        # Sort by severity priority
        severity_order = {
            InsightSeverity.CRITICAL: 0,
            InsightSeverity.CAUTION: 1,
            InsightSeverity.WARNING: 2,
            InsightSeverity.INFO: 3,
            InsightSeverity.SUCCESS: 4
        }
        insights.sort(key=lambda i: severity_order[i.severity])
        
        return insights
    
    def _rule_over_blocking(self, kpis: Dict) -> List[Insight]:
        """Detect over-blocking (too cautious)."""
        approval_rate = kpis['kpis'].get('approval_rate')
        if approval_rate is None:
            return []
        
        if approval_rate < 20:
            return [Insight(
                rule_name="over_blocking",
                severity=InsightSeverity.WARNING,
                message="System Over-Blocking",
                explanation=f"Only {approval_rate}% of decisions approved - system too cautious",
                recommendation="Review policy strictness or lower confidence thresholds"
            )]
        return []
    
    def _rule_over_executing(self, kpis: Dict) -> List[Insight]:
        """Detect over-executing (too permissive)."""
        approval_rate = kpis['kpis'].get('approval_rate')
        if approval_rate is None:
            return []
        
        if approval_rate > 95:
            return [Insight(
                rule_name="over_executing",
                severity=InsightSeverity.CAUTION,
                message="System Over-Executing",
                explanation=f"{approval_rate}% approval rate - almost no safety blocking",
                recommendation="Increase policy strictness for better safety"
            )]
        return []
    
    def _rule_action_dominance(self, kpis: Dict) -> List[Insight]:
        """Detect action repetition."""
        dominance = kpis['kpis'].get('action_dominance')
        if not dominance:
            return []
        
        percent = dominance.get('dominance_percent', 0)
        action = dominance.get('dominant_action', 'unknown')
        
        if percent > 60:
            return [Insight(
                rule_name="action_dominance",
                severity=InsightSeverity.INFO,
                message="Action Repetition Detected",
                explanation=f"'{action}' accounts for {percent}% of all actions",
                recommendation="Check if system stuck in pattern - review action diversity"
            )]
        return []
    
    def _rule_execution_failures(self, kpis: Dict) -> List[Insight]:
        """Detect high execution failure rate."""
        success_rate = kpis['kpis'].get('success_rate')
        if success_rate is None:
            return []
        
        if success_rate < 90:
            return [Insight(
                rule_name="execution_failures",
                severity=InsightSeverity.CRITICAL,
                message="High Execution Failure Rate",
                explanation=f"Only {success_rate}% success - actions not working properly",
                recommendation="Review failed executions logs and fix underlying issues"
            )]
        return []
    
    def _rule_low_activity(self, kpis: Dict) -> List[Insight]:
        """Detect low system activity."""
        events_per_min = kpis['kpis'].get('events_per_minute', 0)
        
        if events_per_min < 2:
            return [Insight(
                rule_name="low_activity",
                severity=InsightSeverity.INFO,
                message="System Activity Low",
                explanation=f"Only {events_per_min} events/min - system may be idle",
                recommendation="Check if autonomic loop is running and interval is appropriate"
            )]
        return []
    
    def _rule_unstable_loop(self, kpis: Dict) -> List[Insight]:
        """Detect loop timing instability."""
        stability = kpis['kpis'].get('loop_stability')
        if stability is None:
            return []
        
        if stability < 0.6:
            return [Insight(
                rule_name="unstable_loop",
                severity=InsightSeverity.WARNING,
                message="Loop Timing Unstable",
                explanation=f"Stability index {stability:.2f} - irregular loop intervals",
                recommendation="Check system CPU/Memory - may indicate performance issues"
            )]
        return []
    
    def _rule_perfect_balance(self, kpis: Dict) -> List[Insight]:
        """Detect optimal system state."""
        approval_rate = kpis['kpis'].get('approval_rate')
        success_rate = kpis['kpis'].get('success_rate')
        
        if approval_rate is None or success_rate is None:
            return []
        
        if 40 <= approval_rate <= 60 and success_rate >= 95:
            return [Insight(
                rule_name="perfect_balance",
                severity=InsightSeverity.SUCCESS,
                message="System Operating Optimally",
                explanation=f"Balanced approval ({approval_rate}%) with high success ({success_rate}%)",
                recommendation=None
            )]
        return []
    
    def _rule_low_confidence(self, kpis: Dict) -> List[Insight]:
        """Detect low decision confidence."""
        avg_confidence = kpis['kpis'].get('avg_confidence')
        if avg_confidence is None:
            return []
        
        if avg_confidence < 0.5:
            return [Insight(
                rule_name="low_confidence",
                severity=InsightSeverity.WARNING,
                message="Low Decision Confidence",
                explanation=f"Average confidence {avg_confidence:.2f} - system uncertain",
                recommendation="System may need more training or clearer policies"
            )]
        return []


# Global instance
_insights_engine = None

def get_insights_engine(kpi_calculator) -> InsightsEngine:
    """Get global insights engine instance."""
    global _insights_engine
    if _insights_engine is None:
        _insights_engine = InsightsEngine(kpi_calculator)
    return _insights_engine
