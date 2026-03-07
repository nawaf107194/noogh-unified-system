"""
Consequence Ledger - Best-Effort Action History

Records action-outcome pairs to filesystem for future reference.

HONESTY DISCLAIMER:
- Storage is filesystem-based and MAY BE LOST or MODIFIED
- There is no enforcement mechanism - only convention
- "Constraints" are advisory scores, not blocks
- Claims of "irreversibility" refer to intent, not technical reality
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set
from enum import Enum

logger = logging.getLogger("unified_core.core.consequence")


@dataclass
class Action:
    """
    An action taken by the system.
    Once committed, its consequences are permanent.
    """
    action_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    action_id: str = field(default_factory=lambda: hashlib.sha256(
        f"{time.time()}:{os.urandom(8).hex()}".encode()
    ).hexdigest()[:16])
    timestamp: float = field(default_factory=time.time)
    
    def __hash__(self):
        return hash(self.action_id)
    
    def matches_pattern(self, pattern: str) -> bool:
        """Check if action matches a pattern."""
        return pattern in self.action_type or pattern in str(self.parameters)


@dataclass
class Outcome:
    """
    The result of an action.
    Outcomes are facts that cannot be changed.
    """
    success: bool
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class Constraint:
    """
    A constraint on future actions derived from past consequences.
    """
    constraint_id: str
    source_consequence: str        # Hash of the consequence that created this
    constraint_type: str           # "block", "require", "limit"
    pattern: str                   # Pattern this constraint matches
    reason: str
    created_at: float = field(default_factory=time.time)
    
    def applies_to(self, action: Action) -> bool:
        """Check if this constraint applies to an action."""
        return action.matches_pattern(self.pattern)


@dataclass
class Consequence:
    """
    Permanent record of action + outcome.
    Once recorded, exists forever.
    """
    consequence_hash: str          # Cryptographic hash proving existence
    action: Action
    outcome: Outcome
    constraints_generated: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "consequence_hash": self.consequence_hash,
            "action_id": self.action.action_id,
            "action_type": self.action.action_type,
            "action_params": self.action.parameters,
            "success": self.outcome.success,
            "result": self.outcome.result,
            "error": self.outcome.error,
            "constraints": self.constraints_generated,
            "timestamp": self.timestamp
        }


class AppendOnlyLedger:
    """
    Append-only storage for consequences with multi-location persistence.
    
    THERE IS NO DELETE METHOD.
    THERE IS NO RESET METHOD.
    THERE IS NO UNDO.
    
    Survives deletion of any storage location (7 locations including system-protected).
    """
    
    
    # UNIFIED CONFIG INTEGRATION
    from unified_core.config import settings
    STORAGE_LOCATIONS = settings.CONSEQUENCE_STORAGE_LOCATIONS

    
    def __init__(self, storage_name: str = "ledger.jsonl"):
        self._storage_name = storage_name
        
        # Create all storage locations
        for loc in self.STORAGE_LOCATIONS:
            os.makedirs(loc, exist_ok=True)
            filepath = os.path.join(loc, storage_name)
            if not os.path.exists(filepath):
                with open(filepath, "w") as f:
                    pass  # Create empty file
    
    def append(self, consequence: Consequence) -> str:
        """
        Append consequence to ALL ledger locations with checksum.
        Returns the hash proving this entry exists.
        """
        data = consequence.to_dict()
        checksum = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        entry = {"data": data, "checksum": checksum}
        entry_json = json.dumps(entry) + "\n"
        
        success_count = 0
        for loc in self.STORAGE_LOCATIONS:
            try:
                filepath = os.path.join(loc, self._storage_name)
                with open(filepath, "a") as f:
                    f.write(entry_json)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to append consequence to {loc}: {e}")
        
        if success_count == 0:
            logger.critical(f"CONSEQUENCE COMMIT FAILED: {consequence.consequence_hash}")
        else:
            logger.info(f"Consequence committed to {success_count}/{len(self.STORAGE_LOCATIONS)} locations: {consequence.consequence_hash}")
        
        return consequence.consequence_hash
    
    def read_all(self) -> List[Dict[str, Any]]:
        """Read and merge consequences from ALL ledger locations with checksum verification."""
        seen_hashes: Dict[str, float] = {}  # hash -> timestamp
        consequences = []
        
        for loc in self.STORAGE_LOCATIONS:
            filepath = os.path.join(loc, self._storage_name)
            if not os.path.exists(filepath):
                continue
                
            location_consequences = self._read_from_file(filepath)
            for data in location_consequences:
                self._merge_entry(consequences, data, seen_hashes)
        
        logger.info(f"Loaded {len(consequences)} consequences from {len(self.STORAGE_LOCATIONS)} locations")
        return consequences

    def _read_from_file(self, filepath: str) -> List[Dict[str, Any]]:
        """Read and validate entries from a single ledger file."""
        valid_data = []
        try:
            with open(filepath, "r") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    entry_data = self._parse_and_verify_line(line, filepath, line_num)
                    if entry_data:
                        valid_data.append(entry_data)
        except Exception as e:
            logger.error(f"Failed to read from {filepath}: {e}")
        return valid_data

    def _parse_and_verify_line(self, line: str, filepath: str, line_num: int) -> Optional[Dict[str, Any]]:
        """Parse JSON line and verify checksum if present."""
        try:
            entry = json.loads(line.strip())
            
            # Support both old format and new format with checksum
            if "checksum" in entry:
                data = entry["data"]
                if not self._verify_checksum(data, entry["checksum"]):
                    logger.critical(f"⚠️ TAMPERING DETECTED in {filepath} line {line_num}!")
                    return None
            else:
                data = entry  # Old format
            
            return data
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {filepath} line {line_num}")
            return None

    def _verify_checksum(self, data: Dict[str, Any], stored_checksum: str) -> bool:
        """Verify checksum of data."""
        computed_checksum = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        return stored_checksum == computed_checksum

    def _merge_entry(self, consequences: List[Dict[str, Any]], data: Dict[str, Any], seen_hashes: Dict[str, float]):
        """Merge a single consequence entry into the result list with deduplication."""
        consequence_hash = data.get("consequence_hash", "")
        timestamp = data.get("timestamp", 0)
        
        # Skip if we already have a newer version
        if consequence_hash in seen_hashes:
            if timestamp <= seen_hashes[consequence_hash]:
                return
        
        seen_hashes[consequence_hash] = timestamp
        
        # Remove old version if exists and append new one
        for i, c in enumerate(consequences):
            if c.get("consequence_hash") == consequence_hash:
                consequences[i] = data
                return
        
        consequences.append(data)
    
    def count(self) -> int:
        """Count entries in ledger."""
        return len(self.read_all())
    
    # NOTE: No delete() method exists
    # NOTE: No reset() method exists
    # NOTE: No undo() method exists


class ConsequenceEngine:
    """
    Makes state transitions irreversible.
    Uses cryptographic commitment: once recorded, cannot be altered.
    Multi-location storage ensures survival.
    """
    
    def __init__(self, storage_name: str = "ledger.jsonl"):
        self._ledger = AppendOnlyLedger(storage_name)
        self._constraints: Dict[str, Constraint] = {}
        self._action_history: Set[str] = set()  # All action IDs ever taken
        
        # Load existing consequences and rebuild constraints
        self._rebuild_from_ledger()
        
        logger.info(f"ConsequenceEngine initialized: {self._ledger.count()} consequences, "
                   f"{len(self._constraints)} constraints")
    
    def _rebuild_from_ledger(self):
        """Rebuild constraint map from persisted consequences."""
        for entry in self._ledger.read_all():
            self._action_history.add(entry["action_id"])
            
            # Rebuild constraints
            if not entry["success"]:
                # Failed actions generate blocking constraints
                constraint = Constraint(
                    constraint_id=f"c_{entry['consequence_hash'][:8]}",
                    source_consequence=entry["consequence_hash"],
                    constraint_type="block",
                    pattern=entry["action_type"],
                    reason=entry.get("error", "Previous failure")
                )
                self._constraints[constraint.constraint_id] = constraint
    
    def commit(self, action: Action, outcome: Outcome) -> str:
        """
        Record action-outcome pair PERMANENTLY.
        Returns hash that proves this consequence exists.
        
        THIS CANNOT BE UNDONE.
        """
        # Generate cryptographic hash
        content = f"{action.action_id}:{action.action_type}:{outcome.success}:{time.time()}"
        consequence_hash = hashlib.sha256(content.encode()).hexdigest()
        
        constraints_generated = []
        
        # If action failed, generate blocking constraint
        if not outcome.success:
            constraint = Constraint(
                constraint_id=f"c_{consequence_hash[:8]}",
                source_consequence=consequence_hash,
                constraint_type="block",
                pattern=action.action_type,
                reason=outcome.error or "Action failed"
            )
            self._constraints[constraint.constraint_id] = constraint
            constraints_generated.append(constraint.constraint_id)
            logger.warning(f"Constraint generated from failure: {constraint.constraint_id}")
        
        # Create consequence record
        consequence = Consequence(
            consequence_hash=consequence_hash,
            action=action,
            outcome=outcome,
            constraints_generated=constraints_generated
        )
        
        # PERMANENT COMMIT
        self._ledger.append(consequence)
        self._action_history.add(action.action_id)
        
        # NeuronFabric Hebbian learning: strengthen/weaken neurons based on outcome
        try:
            from unified_core.core.neuron_fabric import get_neuron_fabric
            fabric = get_neuron_fabric()
            
            # Get recently activated neurons and apply learning
            strongest = fabric.get_strongest_neurons(top_k=10)
            if strongest:
                activated = {n.neuron_id: n.activation_level for n in strongest if n.is_active()}
                if activated:
                    fabric.learn_from_outcome(activated, outcome.success, impact=1.0)
                    logger.info(
                        f"🧬 Hebbian {'reinforcement' if outcome.success else 'weakening'}: "
                        f"{len(activated)} neurons affected"
                    )
        except Exception as e:
            logger.debug(f"NeuronFabric Hebbian learning skipped: {e}")
        
        return consequence_hash
    
    def verify_constraints(self, proposed_action: Action) -> List[Constraint]:
        """
        Check all past consequences that constrain this action.
        Returns list of constraints that MUST be satisfied.
        """
        applicable = []
        for constraint in self._constraints.values():
            if constraint.applies_to(proposed_action):
                applicable.append(constraint)
        return applicable
    
    def is_action_blocked(self, action: Action) -> Tuple[bool, Optional[str]]:
        """
        Return True if this action is blocked by past consequences.
        Also returns the hash of the blocking consequence.
        """
        for constraint in self._constraints.values():
            if constraint.constraint_type == "block" and constraint.applies_to(action):
                return True, constraint.source_consequence
        return False, None
    
    def get_consequence_count(self) -> int:
        """Return total consequences recorded. This only grows."""
        return self._ledger.count()
    
    def get_constraint_count(self) -> int:
        """Return total constraints active. This only grows."""
        return len(self._constraints)
    
    def get_blocked_patterns(self) -> List[str]:
        """Return all patterns that are currently blocked."""
        return [c.pattern for c in self._constraints.values() if c.constraint_type == "block"]
