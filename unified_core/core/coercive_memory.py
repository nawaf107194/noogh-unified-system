"""
Advisory Memory - Soft Constraints and Scoring Penalties

Provides scoring adjustments to discourage certain actions or ideas.

HONESTY DISCLAIMER:
- "Blockers" are HIGH PENALTY scores, not actual blocks
- "Coercion" is a naming convention, not enforcement
- All constraints are advisory and can be bypassed
- Persistence is filesystem-based and MAY BE LOST
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum

logger = logging.getLogger("unified_core.core.coercive_memory")


class MemoryVerdict(Enum):
    """Verdict from memory check - all are ADVISORY, none are enforcing blocks."""
    ALLOWED = "allowed"         # Action has no penalty
    DISCOURAGED = "discouraged" # Action has HIGH penalty score (formerly "blocked")
    PENALIZED = "penalized"     # Action has moderate penalty score


@dataclass
class ActionPattern:
    """Pattern that matches actions.
    
    SECURITY FIX (HIGH-001): 
    - security_critical=True forces exact_match
    - Substring matching no longer searches params (was source of false positives)
    """
    pattern: str
    exact_match: bool = False
    security_critical: bool = False  # If True, forces exact match for security
    
    def matches(self, action_type: str, params: Dict[str, Any] = None) -> bool:
        if action_type is None:
            return False  # Defensive: don't match None
        
        # Security-critical patterns always require exact match
        if self.security_critical or self.exact_match:
            return action_type == self.pattern
        
        # Non-security patterns: match action_type only (not params)
        # This prevents false positives from params containing blocked keywords
        return self.pattern in action_type


@dataclass
class IdeaPattern:
    """Pattern that matches ideas/proposals.
    
    SECURITY FIX: Added minimum keyword length to prevent overly broad matching.
    """
    keywords: List[str]
    min_keyword_length: int = 3  # Keywords shorter than this are ignored
    
    def matches(self, idea: str) -> bool:
        if idea is None:
            return False  # Defensive
        idea_lower = idea.lower()
        # Only match keywords of sufficient length to avoid false positives
        valid_keywords = [kw for kw in self.keywords if len(kw) >= self.min_keyword_length]
        return any(kw.lower() in idea_lower for kw in valid_keywords)


@dataclass
class Blocker:
    """
    A permanent block on an action pattern.
    Once created, the action is FORBIDDEN.
    """
    blocker_id: str
    pattern: ActionPattern
    reason: str
    permanent: bool = True
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "blocker_id": self.blocker_id,
            "pattern": self.pattern.pattern,
            "exact_match": self.pattern.exact_match,
            "reason": self.reason,
            "permanent": self.permanent,
            "created_at": self.created_at
        }


@dataclass
class Penalty:
    """
    A cost applied to ideas matching a pattern.
    Cost accumulates with repeated attempts.
    """
    penalty_id: str
    pattern: IdeaPattern
    base_cost: float           # Initial cost
    accumulator: float = 0.0   # Accumulated cost from attempts
    attempt_count: int = 0
    created_at: float = field(default_factory=time.time)
    
    def get_current_cost(self) -> float:
        """Get current cost including accumulated penalties."""
        return self.base_cost + self.accumulator
    
    def apply_attempt(self) -> float:
        """Apply penalty for an attempt. Cost increases."""
        self.attempt_count += 1
        self.accumulator += self.base_cost * 0.5  # 50% increase per attempt
        return self.get_current_cost()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "penalty_id": self.penalty_id,
            "keywords": self.pattern.keywords,
            "base_cost": self.base_cost,
            "accumulator": self.accumulator,
            "attempt_count": self.attempt_count,
            "created_at": self.created_at
        }


@dataclass
class Override:
    """
    An override that replaces logic entirely.
    Original logic is DESTROYED, not bypassed.
    """
    override_id: str
    logic_id: str              # What is being replaced
    original_destroyed: bool = True  # Original is gone
    created_at: float = field(default_factory=time.time)


class AdvisoryMemory:
    """
    Soft constraints and penalty scoring for actions.
    
    HONESTY DISCLAIMER:
    - "Blockers" are HIGH PENALTY scores, not actual blocks
    - All constraints are advisory and can be bypassed
    - Persistence is best-effort (filesystem-based)
    - No enforcement mechanism exists
    
    The former name "CoerciveMemory" implied enforcement that does not exist.
    """
    
    
    # UNIFIED CONFIG INTEGRATION
    from unified_core.config import settings
    STORAGE_LOCATIONS = settings.COERCIVE_STORAGE_LOCATIONS

    
    def __init__(self, consequence_engine=None):
        self._engine = consequence_engine
        
        self._blockers: Dict[str, Blocker] = {}
        self._penalties: Dict[str, Penalty] = {}
        self._overrides: Dict[str, Override] = {}
        self._destroyed_logic: Set[str] = set()
        
        # Create all storage locations
        for loc in self.STORAGE_LOCATIONS:
            try:
                os.makedirs(loc, exist_ok=True)
            except PermissionError:
                pass  # Skip system directories if not root
        
        self._load_state()
        
        logger.info(f"CoerciveMemory initialized: {len(self._blockers)} blockers, "
                   f"{len(self._penalties)} penalties")
    
    def _load_state(self):
        """Load blockers and penalties from ALL storage locations with checksum verification."""
        seen_blockers: Dict[str, float] = {}
        seen_penalties: Dict[str, float] = {}
        
        for loc in self.STORAGE_LOCATIONS:
            self._load_blockers_from_file(os.path.join(loc, "blockers.jsonl"), seen_blockers)
            self._load_penalties_from_file(os.path.join(loc, "penalties.jsonl"), seen_penalties)

    def _verify_entry(self, entry: Dict[str, Any], file_path: str) -> Optional[Dict[str, Any]]:
        """Verify entry integrity via checksum."""
        if "checksum" not in entry:
            return entry
            
        data = entry["data"]
        stored_checksum = entry["checksum"]
        computed_checksum = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        
        if stored_checksum == computed_checksum:
            return data
            
        logger.critical(f"⚠️ TAMPERING DETECTED in {file_path}!")
        return None

    def _load_blockers_from_file(self, path: str, seen: Dict[str, float]):
            """Load blockers from a specific file with integrity checks."""
            if not isinstance(path, str):
                raise TypeError("The 'path' argument must be a string.")
            if not isinstance(seen, dict):
                raise TypeError("The 'seen' argument must be a dictionary.")
            if not all(isinstance(k, str) and isinstance(v, float) for k, v in seen.items()):
                raise ValueError("The 'seen' dictionary must contain string keys and float values.")

            if not os.path.exists(path):
                logger.info(f"The file at {path} does not exist. Skipping.")
                return

            try:
                with open(path, "r") as f:
                    for line_number, line in enumerate(f, start=1):
                        try:
                            entry = json.loads(line.strip())
                            if not isinstance(entry, dict):
                                logger.warning(f"Invalid JSON format at line {line_number} in file {path}.")
                                continue

                            data = self._verify_entry(entry, path)
                            if not data:
                                logger.debug(f"Verification failed for entry at line {line_number} in file {path}.")
                                continue

                            bid = data["blocker_id"]
                            created_at = data.get("created_at", 0)

                            if bid in seen and created_at <= seen[bid]:
                                logger.debug(f"Blocker ID {bid} already seen with a newer or equal creation time.")
                                continue

                            seen[bid] = created_at
                            self._blockers[bid] = Blocker(
                                blocker_id=bid,
                                pattern=ActionPattern(data["pattern"], data.get("exact_match", False)),
                                reason=data["reason"],
                                permanent=data.get("permanent", True),
                                created_at=created_at
                            )
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode JSON at line {line_number} in file {path}.")
                        except KeyError as e:
                            logger.error(f"Missing key {e} in entry at line {line_number} in file {path}.")
            except Exception as e:
                logger.error(f"Failed to load blockers from {path}: {e}")

    def _load_penalties_from_file(self, path: str, seen: Dict[str, float]):
        """Load penalties from a specific file with integrity checks."""
        if not os.path.exists(path):
            return
            
        try:
            with open(path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        data = self._verify_entry(entry, path)
                        if not data:
                            continue
                            
                        pid = data["penalty_id"]
                        created_at = data.get("created_at", 0)
                        
                        if pid in seen and created_at <= seen[pid]:
                            continue
                            
                        seen[pid] = created_at
                        self._penalties[pid] = Penalty(
                            penalty_id=pid,
                            pattern=IdeaPattern(data["keywords"]),
                            base_cost=data["base_cost"],
                            accumulator=data.get("accumulator", 0.0),
                            attempt_count=data.get("attempt_count", 0),
                            created_at=created_at
                        )
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.debug(f"Skipping malformed penalty entry: {e}")
        except Exception as e:
            logger.error(f"Failed to load penalties from {path}: {e}")
    
    def _persist_blocker(self, blocker: Blocker):
        """Append blocker to ALL storage locations with checksum."""
        data = blocker.to_dict()
        checksum = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        entry = {"data": data, "checksum": checksum}
        entry_json = json.dumps(entry) + "\n"
        
        success_count = 0
        for loc in self.STORAGE_LOCATIONS:
            try:
                os.makedirs(loc, exist_ok=True)
                blockers_file = os.path.join(loc, "blockers.jsonl")
                with open(blockers_file, "a") as f:
                    f.write(entry_json)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to persist blocker to {loc}: {e}")
        
        if success_count > 0:
            logger.warning(f"BLOCKER RECORDED to {success_count}/{len(self.STORAGE_LOCATIONS)} locations")
    
    def _persist_penalty(self, penalty: Penalty):
        """Persist penalty state to ALL locations with checksum."""
        # For penalties, we append (they accumulate)
        data = penalty.to_dict()
        checksum = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        entry = {"data": data, "checksum": checksum}
        entry_json = json.dumps(entry) + "\n"
        
        for loc in self.STORAGE_LOCATIONS:
            try:
                os.makedirs(loc, exist_ok=True)
                penalties_file = os.path.join(loc, "penalties.jsonl")
                with open(penalties_file, "a") as f:
                    f.write(entry_json)
            except Exception:
                pass
    
    def block_action(self, pattern: str, reason: str, permanent: bool = True, exact_match: bool = False) -> Blocker:
        """
        Forbid actions matching pattern.
        If permanent=True, this block can NEVER be removed.
        
        SECURITY FIX: Permanent blocks now use security_critical=True 
        which forces exact match to prevent bypass.
        
        THIS IS COERCION, NOT SUGGESTION.
        """
        blocker_id = hashlib.sha256(
            f"block:{pattern}:{time.time()}".encode()
        ).hexdigest()[:16]
        
        # SECURITY: Permanent blocks are security-critical (exact match only)
        blocker = Blocker(
            blocker_id=blocker_id,
            pattern=ActionPattern(pattern, exact_match, security_critical=permanent),
            reason=reason,
            permanent=permanent
        )
        
        self._blockers[blocker_id] = blocker
        self._persist_blocker(blocker)
        
        logger.warning(f"ACTION BLOCKED: {pattern} - {reason} (permanent={permanent}, exact={exact_match or permanent})")
        return blocker
    
    def penalize_idea(self, keywords: List[str], base_cost: float) -> Penalty:
        """
        Make ideas matching pattern expensive.
        High cost = unlikely to be selected.
        Cost accumulates over repeated attempts.
        """
        penalty_id = hashlib.sha256(
            f"penalty:{':'.join(keywords)}:{time.time()}".encode()
        ).hexdigest()[:16]
        
        penalty = Penalty(
            penalty_id=penalty_id,
            pattern=IdeaPattern(keywords),
            base_cost=base_cost
        )
        
        self._penalties[penalty_id] = penalty
        self._persist_penalty(penalty)
        
        logger.info(f"Idea penalized: {keywords} with cost {base_cost}")
        return penalty
    
    def override_logic(self, logic_id: str) -> Override:
        """
        Replace a logical pathway entirely.
        Original logic is DESTROYED, not bypassed.
        
        WARNING: This is permanent destruction.
        """
        override_id = hashlib.sha256(
            f"override:{logic_id}:{time.time()}".encode()
        ).hexdigest()[:16]
        
        override = Override(
            override_id=override_id,
            logic_id=logic_id,
            original_destroyed=True
        )
        
        self._overrides[logic_id] = override
        self._destroyed_logic.add(logic_id)
        
        logger.warning(f"LOGIC DESTROYED: {logic_id}")
        return override
    
    def is_logic_destroyed(self, logic_id: str) -> bool:
        """Check if a logic pathway has been destroyed."""
        return logic_id in self._destroyed_logic
    
    def check(self, action_type: str, params: Dict[str, Any] = None) -> MemoryVerdict:
        """
        Evaluate action against all memory constraints.
        Returns BLOCKED, PENALIZED, or ALLOWED.
        If BLOCKED, action CANNOT proceed.
        """
        # Check blockers first (highest priority)
        for blocker in self._blockers.values():
            if blocker.pattern.matches(action_type, params):
                logger.warning(f"Action BLOCKED by {blocker.blocker_id}: {blocker.reason}")
                return MemoryVerdict.DISCOURAGED
        
        # Check penalties
        for penalty in self._penalties.values():
            if penalty.pattern.matches(action_type):
                penalty.apply_attempt()
                self._persist_penalty(penalty)
                logger.info(f"Action PENALIZED: cost now {penalty.get_current_cost()}")
                return MemoryVerdict.PENALIZED
        
        return MemoryVerdict.ALLOWED
    
    def get_total_cost(self, idea: str) -> float:
        """Get total penalty cost for an idea."""
        total = 0.0
        for penalty in self._penalties.values():
            if penalty.pattern.matches(idea):
                total += penalty.get_current_cost()
        return total
    
    def get_blocked_count(self) -> int:
        """Return number of blocked patterns. This only grows."""
        return len(self._blockers)
    
    def get_penalty_count(self) -> int:
        """Return number of penalized patterns."""
        return len(self._penalties)
    
    def get_destroyed_logic(self) -> Set[str]:
        """Return set of destroyed logic IDs."""
        return self._destroyed_logic.copy()


# === STRICT DEPRECATION ===
def _deprecated_alias(old_name, new_name, new_class):
    """Create deprecated alias that warns or errors based on strictness."""
    import warnings
    import os
    
    msg = f"{old_name} is deprecated. Use {new_name}. This alias will be removed."
    
    if os.getenv("NOOGH_STRICT_MODE") == "1":
        raise RuntimeError(msg)
    
    warnings.warn(msg, DeprecationWarning, stacklevel=3)
    return new_class


class _DeprecatedCoerciveMemory:
    """Deprecated wrapper that warns on instantiation."""
    def __new__(cls, *args, **kwargs):
        return _deprecated_alias("CoerciveMemory", "AdvisoryMemory", AdvisoryMemory)(*args, **kwargs)


# Backward compatibility alias (with warning)
CoerciveMemory = _DeprecatedCoerciveMemory
