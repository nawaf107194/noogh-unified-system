"""
Goal Audit Engine - Goal Effectiveness Evaluation
Version: 1.0.0
Part of: Self-Directed Layer (Phase 17.5)

Evaluates goal effectiveness over time and proposes reweighting.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger("unified_core.evolution.goal_audit")


@dataclass
class GoalMetrics:
    """Metrics for a single goal."""
    goal_id: str
    goal_type: str
    created_at: float
    completed_at: Optional[float] = None
    success: bool = False
    
    # Cost metrics
    execution_time_ms: float = 0.0
    cycles_used: int = 0
    
    # Outcome metrics
    expected_impact: float = 0.0
    actual_impact: float = 0.0
    
    @property
    def roi(self) -> float:
        """Calculate Return on Investment."""
        if self.execution_time_ms == 0:
            return 0.0
        
        benefit = self.actual_impact if self.success else 0.0
        cost = self.execution_time_ms / 1000.0  # seconds
        
        return benefit / max(cost, 0.001)


class GoalAuditEngine:
    """
    Evaluates goal effectiveness and proposes reweighting.
    
    Features:
    - Track goal execution metrics
    - Calculate ROI for goal types
    - Identify underperforming goal patterns
    - Propose weight adjustments
    """
    
    def __init__(self, world_model=None):
        self.world_model = world_model
        
        # Goal history
        self.goal_metrics: Dict[str, GoalMetrics] = {}
        
        # Aggregated stats by goal type
        self.type_stats: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"count": 0, "success": 0, "total_roi": 0.0, "avg_time_ms": 0.0}
        )
        
        # Weight adjustments
        self.weight_adjustments: Dict[str, float] = {}
        
        logger.info("GoalAuditEngine initialized")
    
    def record_goal_start(
        self,
        goal_id: str,
        goal_type: str,
        expected_impact: float = 1.0
    ):
        """Record when a goal starts execution."""
        metrics = GoalMetrics(
            goal_id=goal_id,
            goal_type=goal_type,
            created_at=time.time(),
            expected_impact=expected_impact
        )
        self.goal_metrics[goal_id] = metrics
        logger.debug(f"Goal started: {goal_id} ({goal_type})")
    
    def record_goal_completion(
        self,
        goal_id: str,
        success: bool,
        actual_impact: float = 0.0,
        cycles_used: int = 0
    ):
        """Record goal completion and update stats."""
        if goal_id not in self.goal_metrics:
            logger.warning(f"Unknown goal completion: {goal_id}")
            return
        
        metrics = self.goal_metrics[goal_id]
        metrics.completed_at = time.time()
        metrics.success = success
        metrics.actual_impact = actual_impact
        metrics.cycles_used = cycles_used
        metrics.execution_time_ms = (metrics.completed_at - metrics.created_at) * 1000
        
        # Update type stats
        stats = self.type_stats[metrics.goal_type]
        stats["count"] += 1
        if success:
            stats["success"] += 1
        stats["total_roi"] += metrics.roi
        stats["avg_time_ms"] = (
            (stats["avg_time_ms"] * (stats["count"] - 1) + metrics.execution_time_ms) 
            / stats["count"]
        )
        
        logger.debug(f"Goal completed: {goal_id} (success={success}, roi={metrics.roi:.2f})")
    
    def get_type_performance(self, goal_type: str) -> Dict[str, float]:
        """Get performance metrics for a goal type."""
        stats = self.type_stats.get(goal_type, {})
        if not stats or stats.get("count", 0) == 0:
            return {"success_rate": 0.0, "avg_roi": 0.0, "avg_time_ms": 0.0}
        
        count = stats["count"]
        return {
            "success_rate": stats["success"] / count,
            "avg_roi": stats["total_roi"] / count,
            "avg_time_ms": stats["avg_time_ms"],
            "total_count": count
        }
    
    def identify_underperformers(self, min_samples: int = 5) -> List[Tuple[str, Dict]]:
        """Identify goal types that are underperforming."""
        underperformers = []
        
        for goal_type, stats in self.type_stats.items():
            if stats["count"] < min_samples:
                continue
            
            performance = self.get_type_performance(goal_type)
            
            # Criteria for underperformance
            if performance["success_rate"] < 0.3:
                underperformers.append((
                    goal_type,
                    {
                        "reason": "low_success_rate",
                        "value": performance["success_rate"],
                        "suggested_weight": 0.5  # Reduce priority
                    }
                ))
            elif performance["avg_roi"] < 0.1:
                underperformers.append((
                    goal_type,
                    {
                        "reason": "low_roi",
                        "value": performance["avg_roi"],
                        "suggested_weight": 0.7
                    }
                ))
        
        return underperformers
    
    def identify_top_performers(self, min_samples: int = 5) -> List[Tuple[str, Dict]]:
        """Identify goal types that are performing well."""
        top_performers = []
        
        for goal_type, stats in self.type_stats.items():
            if stats["count"] < min_samples:
                continue
            
            performance = self.get_type_performance(goal_type)
            
            # Criteria for high performance
            if performance["success_rate"] > 0.8 and performance["avg_roi"] > 1.0:
                top_performers.append((
                    goal_type,
                    {
                        "reason": "high_performance",
                        "success_rate": performance["success_rate"],
                        "avg_roi": performance["avg_roi"],
                        "suggested_weight": 1.5  # Increase priority
                    }
                ))
        
        return top_performers
    
    def propose_weight_adjustments(self) -> Dict[str, float]:
        """
        Propose weight adjustments based on performance analysis.
        
        Returns dict of goal_type -> weight_multiplier
        """
        adjustments = {}
        
        # Identify underperformers
        for goal_type, info in self.identify_underperformers():
            adjustments[goal_type] = info["suggested_weight"]
            logger.info(f"Propose weight reduction for '{goal_type}': {info['suggested_weight']} ({info['reason']})")
        
        # Identify top performers
        for goal_type, info in self.identify_top_performers():
            adjustments[goal_type] = info["suggested_weight"]
            logger.info(f"Propose weight increase for '{goal_type}': {info['suggested_weight']} ({info['reason']})")
        
        self.weight_adjustments = adjustments
        return adjustments
    
    def get_audit_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report."""
        report = {
            "timestamp": time.time(),
            "total_goals_tracked": len(self.goal_metrics),
            "goal_types": {},
            "underperformers": [],
            "top_performers": [],
            "proposed_adjustments": self.weight_adjustments
        }
        
        # Add per-type stats
        for goal_type in self.type_stats:
            report["goal_types"][goal_type] = self.get_type_performance(goal_type)
        
        # Add analysis
        report["underperformers"] = [
            {"type": t, **info} 
            for t, info in self.identify_underperformers()
        ]
        report["top_performers"] = [
            {"type": t, **info}
            for t, info in self.identify_top_performers()
        ]
        
        return report
    
    def get_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        total_goals = len(self.goal_metrics)
        completed_goals = sum(1 for m in self.goal_metrics.values() if m.completed_at)
        successful_goals = sum(1 for m in self.goal_metrics.values() if m.success)
        
        return {
            "total_goals": total_goals,
            "completed_goals": completed_goals,
            "successful_goals": successful_goals,
            "success_rate": successful_goals / max(completed_goals, 1),
            "goal_types_tracked": len(self.type_stats),
            "weight_adjustments": len(self.weight_adjustments)
        }


# Singleton
_audit_engine_instance = None

def get_goal_audit_engine() -> GoalAuditEngine:
    """Get the global GoalAuditEngine instance."""
    global _audit_engine_instance
    if _audit_engine_instance is None:
        _audit_engine_instance = GoalAuditEngine()
    return _audit_engine_instance
