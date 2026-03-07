"""
Feedback Loop System for Noug Neural OS
Tracks performance, analyzes errors, and enables continuous learning
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric for an action"""

    action: str
    success: bool
    duration: float
    resource_usage: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "success": self.success,
            "duration": self.duration,
            "resource_usage": self.resource_usage,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ErrorAnalysis:
    """Analysis of an error"""

    error_type: str
    error_message: str
    action: str
    context: Dict[str, Any]
    root_cause: Optional[str]
    suggested_fix: Optional[str]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "action": self.action,
            "context": self.context,
            "root_cause": self.root_cause,
            "suggested_fix": self.suggested_fix,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class LearningInsight:
    """Insight learned from experience"""

    pattern: str
    confidence: float
    occurrences: int
    success_rate: float
    recommendation: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.pattern,
            "confidence": self.confidence,
            "occurrences": self.occurrences,
            "success_rate": self.success_rate,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp.isoformat(),
        }


class PerformanceTracker:
    """Tracks performance metrics"""

    def __init__(self, max_metrics: int = 10000):
        self.metrics: List[PerformanceMetric] = []
        self.max_metrics = max_metrics
        self.action_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"total": 0, "success": 0, "failed": 0, "total_duration": 0.0, "avg_duration": 0.0}
        )

    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        self.metrics.append(metric)

        # Update stats
        stats = self.action_stats[metric.action]
        stats["total"] += 1
        if metric.success:
            stats["success"] += 1
        else:
            stats["failed"] += 1
        stats["total_duration"] += metric.duration
        stats["avg_duration"] = stats["total_duration"] / stats["total"]

        # Trim if needed
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics :]

    def get_action_stats(self, action: str) -> Dict[str, Any]:
        """Get statistics for a specific action"""
        return dict(self.action_stats.get(action, {}))

    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall performance statistics"""
        total = len(self.metrics)
        if total == 0:
            return {"total": 0, "success_rate": 0}

        successful = sum(1 for m in self.metrics if m.success)
        avg_duration = sum(m.duration for m in self.metrics) / total

        return {
            "total_actions": total,
            "successful_actions": successful,
            "failed_actions": total - successful,
            "success_rate": (successful / total) * 100,
            "avg_duration": avg_duration,
            "unique_actions": len(self.action_stats),
        }

    def get_recent_performance(self, minutes: int = 60) -> Dict[str, Any]:
        """Get performance for recent time window"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = [m for m in self.metrics if m.timestamp > cutoff]

        if not recent:
            return {"count": 0}

        successful = sum(1 for m in recent if m.success)

        return {
            "count": len(recent),
            "successful": successful,
            "failed": len(recent) - successful,
            "success_rate": (successful / len(recent)) * 100,
            "avg_duration": sum(m.duration for m in recent) / len(recent),
        }


class ErrorAnalyzer:
    """Analyzes errors and suggests fixes"""

    def __init__(self):
        self.error_history: List[ErrorAnalysis] = []
        self.error_patterns: Dict[str, int] = defaultdict(int)

    def analyze_error(self, error_type: str, error_message: str, action: str, context: Dict[str, Any]) -> ErrorAnalysis:
        """Analyze an error and suggest fix"""

        # Detect root cause
        root_cause = self._detect_root_cause(error_type, error_message, context)

        # Suggest fix
        suggested_fix = self._suggest_fix(error_type, error_message, root_cause)

        # Create analysis
        analysis = ErrorAnalysis(
            error_type=error_type,
            error_message=error_message,
            action=action,
            context=context,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
        )

        # Record
        self.error_history.append(analysis)
        self.error_patterns[error_type] += 1

        return analysis

    def _detect_root_cause(self, error_type: str, error_message: str, context: Dict[str, Any]) -> Optional[str]:
        """Detect root cause of error"""

        # Common patterns
        if "permission" in error_message.lower():
            return "Insufficient permissions"
        elif "not found" in error_message.lower():
            return "Resource not found"
        elif "timeout" in error_message.lower():
            return "Operation timeout"
        elif "memory" in error_message.lower():
            return "Insufficient memory"
        elif "connection" in error_message.lower():
            return "Network connection issue"

        return "Unknown cause"

    def _suggest_fix(self, error_type: str, error_message: str, root_cause: Optional[str]) -> Optional[str]:
        """Suggest fix for error"""

        if root_cause == "Insufficient permissions":
            return "Request elevated permissions or check access rights"
        elif root_cause == "Resource not found":
            return "Verify resource exists and path is correct"
        elif root_cause == "Operation timeout":
            return "Increase timeout or check system load"
        elif root_cause == "Insufficient memory":
            return "Free up memory or optimize resource usage"
        elif root_cause == "Network connection issue":
            return "Check network connectivity and retry"

        return "Review error details and context"

    def get_common_errors(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get most common error types"""
        sorted_errors = sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)
        return [{"error_type": error, "count": count} for error, count in sorted_errors[:top_n]]

    def get_error_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get error trends over time"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_history if e.timestamp > cutoff]

        error_counts = defaultdict(int)
        for error in recent_errors:
            error_counts[error.error_type] += 1

        return {
            "total_errors": len(recent_errors),
            "unique_error_types": len(error_counts),
            "error_breakdown": dict(error_counts),
        }


class LearningEngine:
    """Extracts insights and learns from experience"""

    def __init__(self):
        self.insights: List[LearningInsight] = []
        self.patterns: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"occurrences": 0, "successes": 0, "failures": 0}
        )

    def learn_from_experience(self, action: str, success: bool, context: Dict[str, Any]):
        """Learn from an action's outcome"""

        # Extract pattern
        pattern = self._extract_pattern(action, context)

        # Update pattern stats
        self.patterns[pattern]["occurrences"] += 1
        if success:
            self.patterns[pattern]["successes"] += 1
        else:
            self.patterns[pattern]["failures"] += 1

        # Generate insight if pattern is significant
        if self.patterns[pattern]["occurrences"] >= 5:
            self._generate_insight(pattern)

    def _extract_pattern(self, action: str, context: Dict[str, Any]) -> str:
        """Extract pattern from action and context"""
        # Simplified pattern extraction
        action_type = action.split()[0] if action else "unknown"
        return f"{action_type}_pattern"

    def _generate_insight(self, pattern: str):
        """Generate learning insight from pattern"""
        stats = self.patterns[pattern]
        success_rate = (stats["successes"] / stats["occurrences"]) * 100

        # Generate recommendation
        if success_rate > 80:
            recommendation = f"Pattern '{pattern}' is highly successful - continue using"
        elif success_rate < 20:
            recommendation = f"Pattern '{pattern}' often fails - consider alternative approach"
        else:
            recommendation = f"Pattern '{pattern}' has mixed results - use with caution"

        insight = LearningInsight(
            pattern=pattern,
            confidence=min(stats["occurrences"] / 100, 1.0),
            occurrences=stats["occurrences"],
            success_rate=success_rate,
            recommendation=recommendation,
        )

        # Update or add insight
        existing = next((i for i in self.insights if i.pattern == pattern), None)
        if existing:
            self.insights.remove(existing)
        self.insights.append(insight)

    def get_insights(self, min_confidence: float = 0.5) -> List[Dict[str, Any]]:
        """Get learning insights above confidence threshold"""
        return [i.to_dict() for i in self.insights if i.confidence >= min_confidence]

    def get_recommendations(self, action: str) -> List[str]:
        """Get recommendations for an action"""
        pattern = self._extract_pattern(action, {})
        insight = next((i for i in self.insights if i.pattern == pattern), None)

        if insight:
            return [insight.recommendation]
        return []


class FeedbackLoop:
    """
    Main feedback loop system that coordinates performance tracking,
    error analysis, and learning
    """

    def __init__(self):
        self.performance_tracker = PerformanceTracker()
        self.error_analyzer = ErrorAnalyzer()
        self.learning_engine = LearningEngine()
        logger.info("FeedbackLoop initialized")

    async def record_action(
        self,
        action: str,
        success: bool,
        duration: float,
        resource_usage: Dict[str, float],
        context: Dict[str, Any],
        error: Optional[Exception] = None,
    ):
        """Record action outcome and learn from it"""

        # Record performance
        metric = PerformanceMetric(
            action=action, success=success, duration=duration, resource_usage=resource_usage, metadata=context
        )
        self.performance_tracker.record_metric(metric)

        # Analyze error if failed
        if not success and error:
            self.error_analyzer.analyze_error(
                error_type=type(error).__name__, error_message=str(error), action=action, context=context
            )

        # Learn from experience
        self.learning_engine.learn_from_experience(action, success, context)

        logger.debug(f"Recorded action: {action} (success={success})")

    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return {
            "overall": self.performance_tracker.get_overall_stats(),
            "recent": self.performance_tracker.get_recent_performance(60),
            "common_errors": self.error_analyzer.get_common_errors(5),
            "error_trends": self.error_analyzer.get_error_trends(24),
            "insights": self.learning_engine.get_insights(0.5),
        }

    async def get_action_feedback(self, action: str) -> Dict[str, Any]:
        """Get feedback for a specific action"""
        return {
            "stats": self.performance_tracker.get_action_stats(action),
            "recommendations": self.learning_engine.get_recommendations(action),
        }

    async def should_retry(self, action: str, error: Exception) -> bool:
        """Determine if action should be retried based on history"""
        stats = self.performance_tracker.get_action_stats(action)

        # Don't retry if historically very unsuccessful
        if stats.get("total", 0) > 10:
            success_rate = (stats.get("success", 0) / stats["total"]) * 100
            if success_rate < 10:
                return False

        # Check if error is retryable
        retryable_errors = ["timeout", "connection", "temporary"]
        error_msg = str(error).lower()
        return any(err in error_msg for err in retryable_errors)
