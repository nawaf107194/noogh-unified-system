"""
Evolution Triggers — Event-Driven Evolution Activation
Version: 3.0.0
Part of: Cognitive Evolution System

Replaces timer-based `cycle % 100` with intelligent triggers that
react to real system events from ObservationStream, CognitiveJournal,
and WorldModel.

Each trigger produces a TriggerEvent with context about WHAT happened,
guiding the evolution engine's target selection.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger("unified_core.evolution.triggers")


class TriggerType(Enum):
    ERROR_SPIKE = "error_spike"
    PERFORMANCE = "performance_degradation"
    GOAL_FAILURE = "goal_failure"
    NEURAL_HEALTH = "neural_health"
    SCHEDULED = "scheduled"
    BELIEF_CONTRADICTION = "belief_contradiction"
    STRATEGIC_GOAL = "strategic_goal"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TriggerEvent:
    """An event that should trigger an evolution cycle."""
    trigger_type: TriggerType
    severity: Severity
    context: Dict[str, Any]
    suggested_targets: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_type": self.trigger_type.value,
            "severity": self.severity.value,
            "context": self.context,
            "suggested_targets": self.suggested_targets,
            "timestamp": self.timestamp
        }


class BaseTrigger:
    """Base class for evolution triggers."""
    
    def __init__(self, name: str, cooldown_seconds: float = 300.0):
        self.name = name
        self.cooldown = cooldown_seconds
        self._last_fired = 0.0
        self._fire_count = 0
    
    def can_fire(self) -> bool:
        return (time.time() - self._last_fired) > self.cooldown
    
    def mark_fired(self):
        self._last_fired = time.time()
        self._fire_count += 1
    
    async def check(self) -> Optional[TriggerEvent]:
        raise NotImplementedError


class ErrorSpikeTrigger(BaseTrigger):
    """Fires when error rate spikes above threshold.
    
    Reads from CognitiveJournal for recent failure entries.
    """
    
    def __init__(self, journal=None, threshold: float = 0.2, window_seconds: float = 120.0):
        super().__init__("error_spike", cooldown_seconds=300.0)
        self._journal = journal
        self._threshold = threshold
        self._window = window_seconds
    
    def set_journal(self, journal):
        self._journal = journal
    
    async def check(self) -> Optional[TriggerEvent]:
        if not self.can_fire() or not self._journal:
            return None
        
        try:
            # Get recent entries from cognitive journal
            recent = self._journal.recall(
                entry_type="failure",
                limit=50,
                min_confidence=0.3
            )
            
            if not recent:
                return None
            
            # Count failures in the time window
            cutoff = time.time() - self._window
            recent_failures = [e for e in recent if e.timestamp > cutoff]
            
            # Also get successes to calculate rate
            successes = self._journal.recall(entry_type="success", limit=50)
            recent_successes = [e for e in successes if e.timestamp > cutoff]
            
            total = len(recent_failures) + len(recent_successes)
            if total < 3:
                return None  # Not enough data
            
            error_rate = len(recent_failures) / total
            
            if error_rate > self._threshold:
                self.mark_fired()
                
                # Extract target files from error contexts
                targets = []
                for entry in recent_failures[:5]:
                    ctx = entry.context or {}
                    if "error" in ctx:
                        # Try to extract file paths from error messages
                        error_str = str(ctx["error"])
                        if ".py" in error_str:
                            targets.append(error_str)
                
                return TriggerEvent(
                    trigger_type=TriggerType.ERROR_SPIKE,
                    severity=Severity.HIGH if error_rate > 0.5 else Severity.MEDIUM,
                    context={
                        "error_rate": round(error_rate, 3),
                        "failure_count": len(recent_failures),
                        "total_events": total,
                        "window_seconds": self._window,
                        "sample_errors": [str(e.content)[:100] for e in recent_failures[:3]]
                    },
                    suggested_targets=targets[:5]
                )
        except Exception as e:
            logger.debug(f"ErrorSpikeTrigger check failed: {e}")
        
        return None


class PerformanceTrigger(BaseTrigger):
    """Fires when system performance degrades.
    
    Reads from WorldModel belief 'system_health'.
    """
    
    def __init__(self, world_model=None, cpu_threshold: float = 85.0, mem_threshold: float = 85.0):
        super().__init__("performance", cooldown_seconds=600.0)
        self._world_model = world_model
        self._cpu_threshold = cpu_threshold
        self._mem_threshold = mem_threshold
        self._sustained_count = 0
        self._sustained_required = 3  # Must be sustained for 3 checks
    
    def set_world_model(self, wm):
        self._world_model = wm
    
    async def check(self) -> Optional[TriggerEvent]:
        if not self.can_fire() or not self._world_model:
            return None
        
        try:
            beliefs = await asyncio.wait_for(
                self._world_model.get_usable_beliefs(), timeout=5
            )
            health_belief = None
            for b in beliefs:
                if "system_health" in b.proposition.lower():
                    health_belief = b
                    break
            
            if not health_belief:
                return None
            
            # Extract health data from belief context
            health = getattr(health_belief, 'context', {}) or {}
            cpu = health.get("cpu_percent", 0)
            mem = health.get("memory_percent", 0)
            
            if cpu > self._cpu_threshold or mem > self._mem_threshold:
                self._sustained_count += 1
            else:
                self._sustained_count = 0
                return None
            
            if self._sustained_count >= self._sustained_required:
                self.mark_fired()
                self._sustained_count = 0
                
                severity = Severity.CRITICAL if (cpu > 95 or mem > 95) else Severity.HIGH
                
                return TriggerEvent(
                    trigger_type=TriggerType.PERFORMANCE,
                    severity=severity,
                    context={
                        "cpu_percent": cpu,
                        "memory_percent": mem,
                        "sustained_checks": self._sustained_required,
                        "neural_alive": health.get("neural_alive", False)
                    }
                )
        except Exception as e:
            logger.debug(f"PerformanceTrigger check failed: {e}")
        
        return None


class GoalFailureTrigger(BaseTrigger):
    """Fires when goals repeatedly fail.
    
    Reads from CognitiveJournal for goal-related failures.
    """
    
    def __init__(self, journal=None, consecutive_threshold: int = 3):
        super().__init__("goal_failure", cooldown_seconds=600.0)
        self._journal = journal
        self._threshold = consecutive_threshold
    
    def set_journal(self, journal):
        self._journal = journal
    
    async def check(self) -> Optional[TriggerEvent]:
        if not self.can_fire() or not self._journal:
            return None
        
        try:
            # Look for goal-related failures
            failures = self._journal.recall(
                topic="goal",
                entry_type="failure",
                limit=10
            )
            
            if len(failures) < self._threshold:
                return None
            
            # Check if recent failures are consecutive (within last 10 min)
            cutoff = time.time() - 600
            recent = [f for f in failures if f.timestamp > cutoff]
            
            if len(recent) >= self._threshold:
                self.mark_fired()
                
                return TriggerEvent(
                    trigger_type=TriggerType.GOAL_FAILURE,
                    severity=Severity.MEDIUM,
                    context={
                        "consecutive_failures": len(recent),
                        "goal_types": list(set(
                            f.context.get("goal_type", "unknown")
                            for f in recent if f.context
                        )),
                        "sample_failures": [f.content[:100] for f in recent[:3]]
                    }
                )
        except Exception as e:
            logger.debug(f"GoalFailureTrigger check failed: {e}")
        
        return None


class BeliefContradictionTrigger(BaseTrigger):
    """Fires when WorldModel contains contradictory beliefs.
    
    This is the most creative trigger — finds where the system's
    understanding conflicts with reality, driving genuine evolution.
    """
    
    def __init__(self, world_model=None):
        super().__init__("belief_contradiction", cooldown_seconds=1800.0)  # 30 min cooldown
        self._world_model = world_model
    
    def set_world_model(self, wm):
        self._world_model = wm
    
    async def check(self) -> Optional[TriggerEvent]:
        if not self.can_fire() or not self._world_model:
            return None
        
        try:
            beliefs = await asyncio.wait_for(
                self._world_model.get_usable_beliefs(), timeout=5
            )
            if len(beliefs) < 2:
                return None
            
            # Find beliefs with very different confidences about related topics
            contradictions = []
            for i, b1 in enumerate(beliefs):
                for b2 in beliefs[i+1:]:
                    # Simple heuristic: same keywords but opposite confidence
                    b1_words = set(b1.proposition.lower().split())
                    b2_words = set(b2.proposition.lower().split())
                    overlap = b1_words & b2_words
                    
                    if len(overlap) >= 2:  # Related topics
                        conf_diff = abs(b1.confidence - b2.confidence)
                        if conf_diff > 0.4:  # Significant confidence gap
                            contradictions.append({
                                "belief_a": b1.proposition[:80],
                                "belief_b": b2.proposition[:80],
                                "confidence_a": b1.confidence,
                                "confidence_b": b2.confidence,
                                "shared_concepts": list(overlap)[:5]
                            })
            
            if contradictions:
                self.mark_fired()
                
                return TriggerEvent(
                    trigger_type=TriggerType.BELIEF_CONTRADICTION,
                    severity=Severity.LOW,
                    context={
                        "contradiction_count": len(contradictions),
                        "top_contradictions": contradictions[:3]
                    }
                )
        except Exception as e:
            logger.debug(f"BeliefContradictionTrigger check failed: {e}")
        
        return None


class LearningInnovationTrigger(BaseTrigger):
    """Fires when autonomous_learner has suggested innovations ready to deploy.

    Reads from /home/noogh/.noogh/innovations.pb and triggers
    evolution when there are enough high-quality suggestions.
    """

    def __init__(self, innovation_file: str = "/home/noogh/.noogh/innovations.pb",
                 min_suggestions: int = 3):
        super().__init__("learning_innovation", cooldown_seconds=900.0)  # 15 min cooldown
        self._innovation_file = innovation_file
        self._min_suggestions = min_suggestions

    async def check(self) -> Optional[TriggerEvent]:
        if not self.can_fire():
            return None

        try:
            import os
            from collections import Counter
            from unified_core.evolution.innovation_storage import InnovationStorage
            from proto_generated.evolution import learning_pb2

            if not os.path.exists(self._innovation_file):
                return None

            # Read all suggested innovations
            storage = InnovationStorage(self._innovation_file)
            all_innovations = storage.get_all()
            suggestions = [i for i in all_innovations if i.status == learning_pb2.INNOVATION_STATUS_SUGGESTED]

            if len(suggestions) < self._min_suggestions:
                return None

            # Count innovation types to find most requested
            type_counts = Counter(s.context.get('original_type', str(s.innovation_type)) for s in suggestions)
            most_common = type_counts.most_common(3)

            # Fire if we have strong signal OR enough diversity
            # v3.1: More lenient - fire if 2+ of same type OR 5+ total (embrace diversity)
            same_type_count = most_common[0][1] if most_common else 0
            fire_condition = (
                same_type_count >= 2 or  # 2+ of same type (was 3)
                len(suggestions) >= 5      # OR 5+ total suggestions (diversity signal)
            )

            logger.info(
                f"🎯 LearningInnovationTrigger check: "
                f"{len(suggestions)} suggested, "
                f"most_common={most_common[0][0]}:{same_type_count}, "
                f"will_fire={fire_condition}"
            )

            if fire_condition:
                self.mark_fired()

                # Get recent suggestions for context
                recent_suggestions = suggestions[-10:]

                return TriggerEvent(
                    trigger_type=TriggerType.SCHEDULED,  # Reuse SCHEDULED type
                    severity=Severity.MEDIUM,
                    context={
                        "reason": "learning_innovations_ready",
                        "total_suggestions": len(suggestions),
                        "top_innovation_types": [
                            {"type": typ, "count": cnt} for typ, cnt in most_common
                        ],
                        "recent_suggestions": [
                            {
                                "type": s.context.get('original_type', str(s.innovation_type)),
                                "rationale": (s.reasoning or s.description)[:100],
                                "triggered_by": s.trigger_event[:80]
                            }
                            for s in recent_suggestions
                        ],
                        "innovation_file": self._innovation_file
                    },
                    suggested_targets=[
                        "unified_core/core/memory_store.py",  # For optimize_memory_queries
                        "unified_core/parallel_processor.py",  # For async_parallel_scan
                        "unified_core/agent_daemon.py"  # For architecture_review
                    ]
                )
        except Exception as e:
            logger.debug(f"LearningInnovationTrigger check failed: {e}")

        return None


class ScheduledTrigger(BaseTrigger):
    """Adaptive timer — cooldown adjusts based on actual cycle duration.

    Instead of a fixed 30-minute wait, the next trigger fires based on
    how long the last evolution cycle took (Brain think + process time):

    - Fast cycle (10s)  → next trigger in ~30s
    - Normal cycle (60s) → next trigger in ~180s
    - Slow cycle (120s)  → next trigger in ~360s

    Formula: next_cooldown = clamp(last_duration × multiplier, min, max)
    """

    def __init__(self, min_interval: float = 60.0, max_interval: float = 1800.0,
                 multiplier: float = 3.0):
        # Start with a short initial cooldown (60s) to fire quickly after startup
        super().__init__("scheduled", cooldown_seconds=min_interval)
        self._min_interval = min_interval
        self._max_interval = max_interval
        self._multiplier = multiplier
        self._last_cycle_duration: float = 0.0
    
    def report_duration(self, duration_seconds: float):
        """Called after a cycle completes to adapt the next cooldown."""
        self._last_cycle_duration = duration_seconds
        # Adaptive: next cooldown = duration × multiplier, clamped to [min, max]
        self.cooldown = max(
            self._min_interval,
            min(self._max_interval, duration_seconds * self._multiplier)
        )
        logger.info(
            f"⏱️ Adaptive cooldown: cycle took {duration_seconds:.1f}s "
            f"→ next trigger in {self.cooldown:.0f}s"
        )
    
    async def check(self) -> Optional[TriggerEvent]:
        if not self.can_fire():
            return None
        
        self.mark_fired()
        return TriggerEvent(
            trigger_type=TriggerType.SCHEDULED,
            severity=Severity.LOW,
            context={
                "reason": "Adaptive evolution check",
                "interval": self.cooldown,
                "last_cycle_duration": self._last_cycle_duration
            }
        )



class StrategicGoalTrigger(BaseTrigger):
    """Fires when human operator sets strategic goals in the database.
    
    Reads from shared_memory.sqlite: system:strategic_goals
    Maps goal descriptions to target files for the evolution engine.
    """
    
    def __init__(self, db_path: str = None, cooldown_seconds: float = 600.0):
        super().__init__("strategic_goal", cooldown_seconds=cooldown_seconds)
        import os
        self._db_path = db_path or os.path.join(
            os.getenv("NOOGH_DATA_DIR", "/home/noogh/projects/noogh_unified_system/src/data"),
            "shared_memory.sqlite"
        )
        self._processed_goals = set()  # Track already-processed goal IDs
    
    async def check(self) -> Optional[TriggerEvent]:
        if not self.can_fire():
            return None
        
        try:
            import sqlite3
            import json
            import os
            
            if not os.path.exists(self._db_path):
                return None
            
            conn = sqlite3.connect(self._db_path, timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT value FROM beliefs WHERE key='system:strategic_goals'")
            row = cur.fetchone()
            conn.close()
            
            if not row:
                return None
            
            goals_data = json.loads(row[0])
            
            # Collect active/planned goals not yet processed
            active_goals = []
            for term in ['short_term', 'long_term']:
                for goal in goals_data.get(term, []):
                    gid = goal.get('id', '')
                    status = goal.get('status', '')
                    if status in ('active', 'planned') and gid not in self._processed_goals:
                        active_goals.append(goal)
            
            if not active_goals:
                return None
            
            # Map goal descriptions to target files
            suggested_targets = []
            goal_keywords = ' '.join(g.get('description', '') for g in active_goals).lower()
            
            # Dashboard/UI targets
            if any(kw in goal_keywords for kw in ['داشبورد', 'dashboard', 'واجهة', 'صفحة', 'تصميم']):
                suggested_targets.extend([
                    'dashboard/templates/index.html',
                    'dashboard/app.py',
                ])
            
            # Chat/Neural Link targets
            if any(kw in goal_keywords for kw in ['دردشة', 'chat', 'ردود', 'محادث', 'neural link']):
                suggested_targets.extend([
                    'neural_engine/identity_v12_9.py',
                    'neural_engine/react_loop.py',
                    'gateway/app/api/dashboard.py',
                ])
            
            # Memory targets
            if any(kw in goal_keywords for kw in ['ذاكرة', 'memory', 'معتقدات', 'beliefs']):
                suggested_targets.extend([
                    'unified_core/core/memory_store.py',
                ])
            
            if not suggested_targets:
                # Generic evolution
                suggested_targets = ['neural_engine/react_loop.py']
            
            # Mark goals as being processed
            for g in active_goals:
                self._processed_goals.add(g.get('id', ''))
            
            self.mark_fired()
            
            return TriggerEvent(
                trigger_type=TriggerType.STRATEGIC_GOAL,
                severity=Severity.HIGH,
                context={
                    "reason": "human_operator_strategic_directive",
                    "active_goals": [
                        {'id': g.get('id'), 'description': g.get('description', '')[:120]}
                        for g in active_goals
                    ],
                    "goal_count": len(active_goals),
                },
                suggested_targets=suggested_targets
            )
        except Exception as e:
            logger.debug(f"StrategicGoalTrigger check failed: {e}")
        
        return None


class EvolutionTriggerSystem:
    """Manages all triggers and checks them efficiently.
    
    Usage:
        triggers = EvolutionTriggerSystem()
        triggers.set_journal(journal)
        triggers.set_world_model(world_model)
        
        # In agent loop (every 10 cycles):
        events = await triggers.check_all()
        for event in events:
            await evolution.handle_trigger(event)
    """
    
    def __init__(self):
        self.triggers: List[BaseTrigger] = [
            ErrorSpikeTrigger(),
            # v21: DISABLED — PerformanceTrigger and BeliefContradictionTrigger
            # call world_model.get_usable_beliefs() which blocks the event loop
            # indefinitely (synchronous DB I/O inside async def).
            # asyncio.wait_for() cannot cancel them.
            # PerformanceTrigger(),
            # BeliefContradictionTrigger(),
            GoalFailureTrigger(),
            LearningInnovationTrigger(),  # Apply autonomous learning
            StrategicGoalTrigger(),       # Reads human operator's strategic goals from DB
            ScheduledTrigger(),
        ]
        self._total_events_fired = 0
        logger.info("🎯 EvolutionTriggerSystem initialized with %d triggers", len(self.triggers))
    
    def set_journal(self, journal):
        """Wire CognitiveJournal to triggers that need it."""
        for t in self.triggers:
            if hasattr(t, 'set_journal'):
                t.set_journal(journal)
    
    def set_world_model(self, world_model):
        """Wire WorldModel to triggers that need it."""
        for t in self.triggers:
            if hasattr(t, 'set_world_model'):
                t.set_world_model(world_model)
    
    async def check_all(self) -> List[TriggerEvent]:
        """Check all triggers and return any fired events.
        
        This is lightweight — designed to be called frequently (every ~20s).
        Each trigger has its own cooldown to prevent flooding.
        v21: Per-trigger 10s timeout to prevent blocking the daemon.
        """
        events = []
        
        for trigger in self.triggers:
            try:
                logger.info(f"  🔍 Checking trigger: {trigger.name}")
                # v21: Use wait_for with 10s timeout to prevent blocking
                event = await asyncio.wait_for(trigger.check(), timeout=10)
                logger.info(f"  ✅ Trigger {trigger.name} done")
                if event:
                    events.append(event)
                    self._total_events_fired += 1
                    logger.info(
                        f"🎯 Trigger fired: {event.trigger_type.value} "
                        f"[{event.severity.value}] — {self._summarize(event)}"
                    )
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Trigger {trigger.name} timed out (>10s) — skipping")
            except Exception as e:
                logger.info(f"  ⚠️ Trigger {trigger.name} error: {e}")
        
        return events
    
    def _summarize(self, event: TriggerEvent) -> str:
        """One-line summary of a trigger event."""
        ctx = event.context
        if event.trigger_type == TriggerType.ERROR_SPIKE:
            return f"error_rate={ctx.get('error_rate', '?')}"
        elif event.trigger_type == TriggerType.PERFORMANCE:
            return f"CPU={ctx.get('cpu_percent', '?')}% MEM={ctx.get('memory_percent', '?')}%"
        elif event.trigger_type == TriggerType.GOAL_FAILURE:
            return f"{ctx.get('consecutive_failures', '?')} consecutive goal failures"
        elif event.trigger_type == TriggerType.BELIEF_CONTRADICTION:
            return f"{ctx.get('contradiction_count', '?')} contradictions found"
        return "scheduled check"
    
    def report_cycle_duration(self, duration_seconds: float):
        """Feed cycle duration to the ScheduledTrigger for adaptive cooldown."""
        for t in self.triggers:
            if isinstance(t, ScheduledTrigger):
                t.report_duration(duration_seconds)
                break
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_triggers": len(self.triggers),
            "total_events_fired": self._total_events_fired,
            "trigger_states": {
                t.name: {
                    "fire_count": t._fire_count,
                    "last_fired": t._last_fired,
                    "can_fire": t.can_fire()
                }
                for t in self.triggers
            }
        }
