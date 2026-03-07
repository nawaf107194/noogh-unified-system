"""
Evolution Memory — Learning from Proposal Outcomes
Version: 3.0.0
Part of: Cognitive Evolution System

Tracks which proposals succeeded or failed, learns patterns,
and advises the evolution engine on strategy selection.

Integrates with ConsequenceEngine for permanent record-keeping
and ScarTissue for pain-based file protection.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("unified_core.evolution.memory")

# v3.1: Bridge to UnifiedMemoryStore for cross-system learning
_unified_memory = None
def _get_unified_memory():
    global _unified_memory
    if _unified_memory is None:
        try:
            from unified_core.core.memory_store import UnifiedMemoryStore
            _unified_memory = UnifiedMemoryStore()
            logger.info("🔗 EvolutionMemory connected to UnifiedMemoryStore")
        except Exception as e:
            logger.warning(f"UnifiedMemoryStore not available for evolution bridge: {e}")
    return _unified_memory

# Persistence location
MEMORY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "evolution_memory"
)


@dataclass
class ProposalOutcome:
    """Record of a proposal's result."""
    proposal_id: str
    proposal_type: str        # "code", "config", "policy"
    target_area: str           # file or component name
    trigger_type: str          # what triggered this proposal
    success: bool
    impact_delta: float = 0.0  # positive = improvement, negative = regression
    confidence: float = 0.5
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "proposal_type": self.proposal_type,
            "target_area": self.target_area,
            "trigger_type": self.trigger_type,
            "success": self.success,
            "impact_delta": self.impact_delta,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "details": self.details
        }


@dataclass
class Strategy:
    """A learned strategy pattern."""
    name: str
    success_rate: float
    total_attempts: int
    avg_impact: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "success_rate": round(self.success_rate, 3),
            "total_attempts": self.total_attempts,
            "avg_impact": round(self.avg_impact, 3)
        }


class EvolutionMemory:
    """Learns from evolution outcomes to improve future proposals.
    
    Learning Rules:
    - If a file has 2+ rollbacks → mark as "fragile" for 24h
    - Track success rate per proposal_type and trigger_type
    - Identify which strategies produce the best impact scores
    - Feed insights back to evolution engine for strategy selection
    """
    
    def __init__(self, memory_dir: str = None):
        self._dir = memory_dir or MEMORY_DIR
        os.makedirs(self._dir, exist_ok=True)
        self._outcomes_file = os.path.join(self._dir, "outcomes.jsonl")
        self._fragile_file = os.path.join(self._dir, "fragile_files.json")
        
        # In-memory caches
        self._outcomes: List[ProposalOutcome] = []
        self._fragile_files: Dict[str, float] = {}  # filepath → expiry timestamp
        
        # Load existing data
        self._load()
        
        logger.info(f"🧠 EvolutionMemory initialized: {len(self._outcomes)} outcomes, "
                     f"{len(self._fragile_files)} fragile files")
    
    def record_outcome(self, outcome: ProposalOutcome):
        """Record a proposal outcome and update learning state.
        
        v3.1: Also bridges to UnifiedMemoryStore so WorldModel/Agents
        can access evolution outcomes as shared experiences.
        """
        self._outcomes.append(outcome)
        self._save_outcome(outcome)
        
        # Learning: track fragile files
        if not outcome.success:
            self._mark_fragile(outcome.target_area)
        
        # v3.1: Bridge to UnifiedMemoryStore (non-blocking, best-effort)
        try:
            mem = _get_unified_memory()
            if mem:
                import asyncio
                # Use sync _record_experience_sync (direct) or async record_experience
                exp_id = f"evo_{outcome.proposal_id}"
                exp_context = json.dumps({
                    "proposal_type": outcome.proposal_type,
                    "target_area": outcome.target_area,
                    "trigger_type": outcome.trigger_type,
                    "confidence": outcome.confidence,
                })
                exp_action = f"evolution_{outcome.proposal_type}"
                exp_outcome = json.dumps({
                    "success": outcome.success,
                    "impact_delta": outcome.impact_delta,
                    "details": outcome.details,
                })
                exp_success = outcome.success
                
                if hasattr(mem, '_record_experience_sync'):
                    mem._record_experience_sync(exp_id, exp_context, exp_action, exp_outcome, exp_success)
                else:
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(mem.record_experience(exp_id, exp_context, exp_action, exp_outcome, exp_success))
                    except RuntimeError:
                        pass  # No event loop; skip async bridge
                logger.debug(f"🔗 Bridged outcome {outcome.proposal_id} to UnifiedMemoryStore")
        except Exception as e:
            logger.debug(f"UnifiedMemoryStore bridge failed (non-critical): {e}")
        
        logger.info(
            f"🧠 Recorded: {outcome.proposal_id} "
            f"{'✅' if outcome.success else '❌'} "
            f"(impact={outcome.impact_delta:+.2f})"
        )
    
    def get_success_rate(self, proposal_type: str = None, trigger_type: str = None) -> float:
        """Get success rate, optionally filtered by type."""
        filtered = self._outcomes
        
        if proposal_type:
            filtered = [o for o in filtered if o.proposal_type == proposal_type]
        if trigger_type:
            filtered = [o for o in filtered if o.trigger_type == trigger_type]
        
        if not filtered:
            return 0.5  # No data → neutral
        
        successes = sum(1 for o in filtered if o.success)
        return successes / len(filtered)
    
    def get_best_strategies(self, limit: int = 5) -> List[Strategy]:
        """Identify which proposal_type + trigger_type combos work best."""
        combos: Dict[str, List[ProposalOutcome]] = {}
        
        for o in self._outcomes:
            key = f"{o.proposal_type}:{o.trigger_type}"
            combos.setdefault(key, []).append(o)
        
        strategies = []
        for name, outcomes in combos.items():
            if len(outcomes) < 2:
                continue  # Not enough data
            
            success_rate = sum(1 for o in outcomes if o.success) / len(outcomes)
            avg_impact = sum(o.impact_delta for o in outcomes) / len(outcomes)
            
            strategies.append(Strategy(
                name=name,
                success_rate=success_rate,
                total_attempts=len(outcomes),
                avg_impact=avg_impact
            ))
        
        # Sort by success rate × impact
        strategies.sort(key=lambda s: s.success_rate * max(s.avg_impact, 0.1), reverse=True)
        return strategies[:limit]
    
    def should_skip_target(self, filepath: str) -> bool:
        """Check if a file is marked fragile (recently caused failures)."""
        self._prune_expired_fragile()
        
        # Check exact match and parent directories
        for fragile_path, expiry in self._fragile_files.items():
            if filepath == fragile_path or fragile_path in filepath:
                if time.time() < expiry:
                    logger.info(f"🩹 Skipping fragile target: {filepath}")
                    return True
        
        return False
    
    def get_scar_penalty(self, filepath: str) -> float:
        """Get risk penalty for a file based on past failures.
        
        Returns 0-30 penalty to add to risk score.
        """
        failure_count = sum(
            1 for o in self._outcomes
            if o.target_area == filepath and not o.success
        )
        
        # Each failure adds 5 risk, capped at 30
        return min(failure_count * 5, 30)
    
    def get_recent_failures(self, target_area: str, function: str = None, limit: int = 3) -> list:
        """v9: Get recent failure reasons for a file/function.
        
        Returns list of error strings (most recent first) to inject
        into Brain prompt so it learns from past rejections.
        """
        reasons = []
        for outcome in sorted(self._outcomes, key=lambda o: o.timestamp, reverse=True):
            if outcome.target_area == target_area and not outcome.success:
                if function and outcome.details.get("function") != function:
                    continue
                error = outcome.details.get('error', '')
                if error and error not in reasons:
                    reasons.append(error)
                if len(reasons) >= limit:
                    break
        return reasons
    
    def get_recommendation(self, trigger_type: str) -> Dict[str, Any]:
        """Get strategy recommendation based on what's worked before."""
        strategies = self.get_best_strategies()
        
        # Find strategies matching this trigger type
        matching = [s for s in strategies if trigger_type in s.name]
        
        if matching:
            best = matching[0]
            return {
                "strategy": best.name,
                "confidence": best.success_rate,
                "basis": f"{best.total_attempts} past attempts, {best.success_rate:.0%} success"
            }
        
        return {
            "strategy": "explore",
            "confidence": 0.5,
            "basis": "No history for this trigger type — exploring"
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Return memory statistics."""
        return {
            "total_outcomes": len(self._outcomes),
            "overall_success_rate": self.get_success_rate(),
            "fragile_files": len(self._fragile_files),
            "strategies": [s.to_dict() for s in self.get_best_strategies(3)],
            "recent_outcomes": [
                o.to_dict() for o in self._outcomes[-5:]
            ]
        }
    
    def get_success_patterns(self) -> Dict[str, Any]:
        """Analyze outcomes to find success patterns.
        
        v5.0: Identifies which types of changes consistently succeed,
        enabling the CreativeEvolutionAgent to prioritize effective strategies.
        
        Returns:
            Dict with top_types, top_triggers, and avg_impact per category
        """
        if len(self._outcomes) < 3:
            return {"status": "insufficient_data", "count": len(self._outcomes)}
        
        # Success rate by proposal type
        type_stats: Dict[str, Dict] = {}
        for o in self._outcomes:
            stats = type_stats.setdefault(o.proposal_type, {"success": 0, "fail": 0, "impact": 0.0})
            if o.success:
                stats["success"] += 1
                stats["impact"] += o.impact_delta
            else:
                stats["fail"] += 1
        
        # Success rate by trigger type
        trigger_stats: Dict[str, Dict] = {}
        for o in self._outcomes:
            stats = trigger_stats.setdefault(o.trigger_type, {"success": 0, "fail": 0})
            if o.success:
                stats["success"] += 1
            else:
                stats["fail"] += 1
        
        # Build ranked results
        top_types = sorted(
            [{"type": k, "rate": v["success"] / max(v["success"] + v["fail"], 1), 
              "total": v["success"] + v["fail"], "avg_impact": v["impact"] / max(v["success"], 1)}
             for k, v in type_stats.items()],
            key=lambda x: x["rate"], reverse=True
        )
        
        top_triggers = sorted(
            [{"trigger": k, "rate": v["success"] / max(v["success"] + v["fail"], 1),
              "total": v["success"] + v["fail"]}
             for k, v in trigger_stats.items()],
            key=lambda x: x["rate"], reverse=True
        )
        
        return {
            "top_types": top_types[:5],
            "top_triggers": top_triggers[:5],
            "total_outcomes": len(self._outcomes),
            "overall_success_rate": self.get_success_rate()
        }
    
    def suggest_similar_targets(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Suggest files similar to those with successful improvements.
        
        v5.0: Finds directories/modules where improvements have worked before
        and suggests other files in the same areas that haven't been touched.
        
        Returns:
            List of dicts with {"directory", "successful_count", "untouched_files"}
        """
        # Find directories with successful outcomes
        successful_dirs: Dict[str, int] = {}
        touched_files: set = set()
        
        for o in self._outcomes:
            if o.success and o.target_area:
                touched_files.add(o.target_area)
                dir_path = os.path.dirname(o.target_area)
                if dir_path:
                    successful_dirs[dir_path] = successful_dirs.get(dir_path, 0) + 1
        
        if not successful_dirs:
            return []
        
        # For top successful directories, find untouched .py files
        suggestions = []
        for dir_path, count in sorted(successful_dirs.items(), key=lambda x: x[1], reverse=True):
            if not os.path.isdir(dir_path):
                continue
            
            try:
                untouched = []
                for f in os.listdir(dir_path):
                    if f.endswith('.py') and not f.startswith('_'):
                        fpath = os.path.join(dir_path, f)
                        if fpath not in touched_files:
                            untouched.append(f)
                
                if untouched:
                    suggestions.append({
                        "directory": dir_path,
                        "successful_count": count,
                        "untouched_files": untouched[:5]  # Cap per directory
                    })
            except OSError:
                continue
        
        return suggestions[:limit]
    
    # --- Private methods ---
    
    def _mark_fragile(self, filepath: str, duration_hours: float = 24.0):
        """Mark a file as fragile after a failure."""
        expiry = time.time() + (duration_hours * 3600)
        self._fragile_files[filepath] = expiry
        self._save_fragile()
        logger.warning(f"🩹 Marked fragile: {filepath} (for {duration_hours}h)")
    
    def _prune_expired_fragile(self):
        """Remove expired fragile markers."""
        now = time.time()
        expired = [k for k, v in self._fragile_files.items() if v < now]
        for k in expired:
            del self._fragile_files[k]
        if expired:
            self._save_fragile()
    
    def _save_outcome(self, outcome: ProposalOutcome):
        """Append outcome to JSONL file."""
        try:
            with open(self._outcomes_file, 'a') as f:
                f.write(json.dumps(outcome.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to save outcome: {e}")
    
    def _save_fragile(self):
        """Save fragile files map."""
        try:
            with open(self._fragile_file, 'w') as f:
                json.dump(self._fragile_files, f)
        except Exception as e:
            logger.error(f"Failed to save fragile files: {e}")
    
    def _load(self):
        """Load existing outcomes and fragile files from disk."""
        # Load outcomes
        if os.path.exists(self._outcomes_file):
            try:
                with open(self._outcomes_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            self._outcomes.append(ProposalOutcome(**data))
            except Exception as e:
                logger.warning(f"Failed to load outcomes: {e}")
        
        # Load fragile files
        if os.path.exists(self._fragile_file):
            try:
                with open(self._fragile_file, 'r') as f:
                    self._fragile_files = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load fragile files: {e}")


# Singleton
_memory_instance: Optional[EvolutionMemory] = None

def get_evolution_memory() -> EvolutionMemory:
    """Get or create global EvolutionMemory instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = EvolutionMemory()
    return _memory_instance
