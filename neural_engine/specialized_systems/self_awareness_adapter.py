"""
Self-Awareness Adapter - Analyzes autonomic system behavior
Provides insights into decision patterns, policy effectiveness, and trends
"""

import logging
from typing import Dict, Any, List, Tuple
from collections import Counter
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SelfAwarenessAdapter:
    """
    Analyzes autonomic system behavior through event stream
    Implements: OBSERVE → ASSESS → PROPOSE pattern for self-analysis
    """
    
    def __init__(self):
        """Initialize self-awareness adapter"""
        from neural_engine.autonomic_system.event_stream import get_event_stream
        
        self.stream = get_event_stream()
        self.analysis_history = []
        
        logger.info("✅ SelfAwarenessAdapter initialized")
    
    # ========== OBSERVE LAYER ==========
    
    def observe(self, window_seconds: int = 300) -> Dict[str, Any]:
        """
        Observe recent autonomic behavior
        
        Args:
            window_seconds: Time window to analyze (default: 300 = 5 minutes)
            
        Returns:
            Recent events and metadata
        """
        try:
            # Get all recent events (EventStream has them in memory)
            all_events = self.stream.get_recent_events(limit=1000)
            
            # Filter by time window
            cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
            
            filtered_events = []
            for event in all_events:
                event_time = datetime.fromisoformat(event['timestamp'])
                if event_time >= cutoff_time:
                    filtered_events.append(event)
            
            observation = {
                "window_seconds": window_seconds,
                "total_events": len(filtered_events),
                "events": filtered_events,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"📊 Observed {len(filtered_events)} events in {window_seconds}s window")
            return observation
            
        except Exception as e:
            logger.error(f"❌ Observation failed: {e}")
            return {
                "window_seconds": window_seconds,
                "total_events": 0,
                "events": [],
                "error": str(e)
            }
    
    # ========== ASSESS LAYER ==========
    
    def assess(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess autonomic behavior patterns
        
        Args:
            observation: Events from observe()
            
        Returns:
            Behavioral assessment with metrics and insights
        """
        events = observation.get("events", [])
        
        # Categorize events by type
        events_by_type = {
            "observation": [],
            "assessment": [],
            "proposal": [],
            "decision": [],
            "execution": []
        }
        
        for event in events:
            event_type = event.get("type")
            if event_type in events_by_type:
                events_by_type[event_type].append(event)
        
        # Analyze decisions
        decisions = events_by_type["decision"]
        decision_analysis = self._analyze_decisions(decisions)
        
        # Analyze executions
        executions = events_by_type["execution"]
        execution_analysis = self._analyze_executions(executions)
        
        # Analyze observations
        observations = events_by_type["observation"]
        health_analysis = self._analyze_health(observations)
        
        # Overall assessment
        assessment = {
            "window_seconds": observation.get("window_seconds", 0),
            "total_events": observation.get("total_events", 0),
            "events_by_type": {k: len(v) for k, v in events_by_type.items()},
            "decision_analysis": decision_analysis,
            "execution_analysis": execution_analysis,
            "health_analysis": health_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in history
        self.analysis_history.append(assessment)
        if len(self.analysis_history) > 100:
            self.analysis_history.pop(0)
        
        logger.info(f"🔍 Assessment: {decision_analysis['total_decisions']} decisions, "
                   f"{decision_analysis['approval_rate']:.1%} approved")
        
        return assessment
    
    def _analyze_decisions(self, decisions: List[Dict]) -> Dict[str, Any]:
        """Analyze decision patterns"""
        if not decisions:
            return {
                "total_decisions": 0,
                "approved": 0,
                "blocked": 0,
                "approval_rate": 0.0,
                "top_actions": [],
                "confidence_avg": 0.0
            }
        
        approved = sum(1 for d in decisions if d.get("payload", {}).get("approved") is True)
        blocked = sum(1 for d in decisions if d.get("payload", {}).get("approved") is False)
        
        # Top actions
        actions = [d.get("payload", {}).get("action") for d in decisions 
                  if d.get("payload", {}).get("action")]
        action_counts = Counter(actions)
        top_actions = action_counts.most_common(5)
        
        # Average confidence
        confidences = [d.get("payload", {}).get("confidence", 0) for d in decisions]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "total_decisions": len(decisions),
            "approved": approved,
            "blocked": blocked,
            "approval_rate": approved / max(1, approved + blocked),
            "top_actions": top_actions,
            "confidence_avg": avg_confidence
        }
    
    def _analyze_executions(self, executions: List[Dict]) -> Dict[str, Any]:
        """Analyze execution patterns"""
        if not executions:
            return {
                "total_executions": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "top_executed_actions": []
            }
        
        successful = sum(1 for e in executions if e.get("payload", {}).get("success") is True)
        failed = sum(1 for e in executions if e.get("payload", {}).get("success") is False)
        
        # Top executed actions
        actions = [e.get("payload", {}).get("action") for e in executions 
                  if e.get("payload", {}).get("action")]
        action_counts = Counter(actions)
        top_actions = action_counts.most_common(5)
        
        return {
            "total_executions": len(executions),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / max(1, len(executions)),
            "top_executed_actions": top_actions
        }
    
    def _analyze_health(self, observations: List[Dict]) -> Dict[str, Any]:
        """Analyze system health trends"""
        if not observations:
            return {
                "observations": 0,
                "avg_cpu": 0.0,
                "avg_memory": 0.0,
                "health_statuses": {}
            }
        
        # Extract metrics
        cpu_values = [o.get("payload", {}).get("cpu_percent", 0) for o in observations]
        mem_values = [o.get("payload", {}).get("memory_percent", 0) for o in observations]
        health_statuses = [o.get("payload", {}).get("health_status", "unknown") for o in observations]
        
        avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
        avg_memory = sum(mem_values) / len(mem_values) if mem_values else 0.0
        
        status_counts = Counter(health_statuses)
        
        return {
            "observations": len(observations),
            "avg_cpu": avg_cpu,
            "avg_memory": avg_memory,
            "health_statuses": dict(status_counts)
        }
    
    # ========== PROPOSE LAYER ==========
    
    def propose_actions(self, assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Propose self-improvement actions based on assessment
        
        Args:
            assessment: Behavioral assessment
            
        Returns:
            List of proposed improvements
        """
        proposals = []
        
        decision_analysis = assessment.get("decision_analysis", {})
        execution_analysis = assessment.get("execution_analysis", {})
        total_decisions = decision_analysis.get("total_decisions", 0)
        approval_rate = decision_analysis.get("approval_rate", 0)
        
        # Insight 1: Over-blocking (too restrictive)
        if total_decisions >= 20 and approval_rate < 0.2:
            proposals.append({
                "action": "review_policy_thresholds",
                "confidence": 0.9,
                "auto_execute": False,
                "reason": f"Low approval rate ({approval_rate:.1%}) suggests over-blocking. Review policy thresholds.",
                "severity": "medium",
                "impact": "May be blocking legitimate actions"
            })
        
        # Insight 2: Over-executing (too permissive)
        if total_decisions >= 20 and approval_rate > 0.95:
            proposals.append({
                "action": "add_manual_gates",
                "confidence": 0.7,
                "auto_execute": False,
                "reason": f"High approval rate ({approval_rate:.1%}) suggests over-executing. Consider stricter policies.",
                "severity": "low",
                "impact": "May need more safety gates"
            })
        
        # Insight 3: Execution failures
        success_rate = execution_analysis.get("success_rate", 1.0)
        if execution_analysis.get("total_executions", 0) >= 5 and success_rate < 0.9:
            proposals.append({
                "action": "investigate_failures",
                "confidence": 0.95,
                "auto_execute": False,
                "reason": f"Execution success rate ({success_rate:.1%}) is below threshold. Investigate failures.",
                "severity": "high",
                "impact": "Actions are failing to execute properly"
            })
        
        # Insight 4: Top actions analysis
        top_actions = decision_analysis.get("top_actions", [])
        if top_actions:
            most_common_action, count = top_actions[0]
            if count > total_decisions * 0.5:  # More than 50% of decisions
                proposals.append({
                    "action": "review_action_dominance",
                    "confidence": 0.8,
                    "auto_execute": False,
                    "reason": f"Action '{most_common_action}' dominates ({count}/{total_decisions} decisions). Review if this is expected.",
                    "severity": "low",
                    "impact": "May indicate repetitive behavior"
                })
        
        # Insight 5: Low confidence decisions
        avg_confidence = decision_analysis.get("confidence_avg", 1.0)
        if total_decisions >= 10 and avg_confidence < 0.7:
            proposals.append({
                "action": "improve_confidence_scoring",
                "confidence": 0.75,
                "auto_execute": False,
                "reason": f"Average decision confidence ({avg_confidence:.2f}) is low. Review confidence scoring logic.",
                "severity": "medium",
                "impact": "Decisions may be uncertain"
            })
        
        logger.info(f"💡 Proposed {len(proposals)} self-improvement actions")
        return proposals
    
    # ========== UTILITY ==========
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter status"""
        return {
            "adapter": "SelfAwareness",
            "status": "operational",
            "analyses_performed": len(self.analysis_history)
        }
    
    def get_summary(self, window_seconds: int = 300) -> Dict[str, Any]:
        """
        Get complete behavioral summary
        
        Args:
            window_seconds: Analysis window
            
        Returns:
            Observation + Assessment + Proposals
        """
        observation = self.observe(window_seconds=window_seconds)
        assessment = self.assess(observation)
        proposals = self.propose_actions(assessment)
        
        return {
            "observation": observation,
            "assessment": assessment,
            "proposals": proposals,
            "timestamp": datetime.now().isoformat()
        }


# Singleton instance
_adapter_instance = None


def get_self_awareness_adapter() -> SelfAwarenessAdapter:
    """Get singleton self-awareness adapter"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = SelfAwarenessAdapter()
    return _adapter_instance
