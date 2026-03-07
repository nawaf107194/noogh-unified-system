"""
Failure Record - Failure Tracking with ENFORCEMENT

Records failures and applies penalties that block similar actions.

ENFORCEMENT MODES:
- enforce_mode=True (default): Scars BLOCK actions from executing
- enforce_mode=False: Scars are advisory penalties only

Persistence is filesystem-based across multiple locations.
GPU memory sacrifice is Python-level (process restart recovers it).
"""

import hashlib
import json
import logging
import os
import time
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("unified_core.core.scar")


@dataclass
class Failure:
    """
    A failure event that will cause scarring.
    """
    failure_id: str
    action_type: str
    action_params: Dict[str, Any]
    error_message: str
    belief_ids_involved: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "action_type": self.action_type,
            "action_params": self.action_params,
            "error_message": self.error_message,
            "belief_ids_involved": self.belief_ids_involved,
            "timestamp": self.timestamp
        }


@dataclass 
class Scar:
    """
    Permanent damage from a failure.
    
    A scar is IRREVERSIBLE. It constrains all future decisions.
    """
    scar_id: str
    source_failure_id: str
    
    # Effects of this scar
    actions_blocked: List[str]      # Action patterns now blocked
    beliefs_falsified: List[str]    # Belief IDs now falsified
    ideas_penalized: List[str]      # Keywords now penalized
    
    # Metadata
    depth: float = 1.0              # Severity of scar
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scar_id": self.scar_id,
            "source_failure_id": self.source_failure_id,
            "actions_blocked": self.actions_blocked,
            "beliefs_falsified": self.beliefs_falsified,
            "ideas_penalized": self.ideas_penalized,
            "depth": self.depth,
            "created_at": self.created_at
        }


class FailureRecord:
    """
    Failure tracking with enforcement capability.
    
    ENFORCEMENT MODE (enable_enforcement=True):
    - Scars BLOCK actions from executing (DecisionScorer checks before scoring)
    - is_action_blocked() returns True for scarred actions
    - CoerciveMemory blocks are permanent
    
    ADVISORY MODE (enable_enforcement=False):
    - Scars apply HIGH PENALTY scores
    - Actions can still be selected with enough weight
    
    Persistence: Filesystem-based, multiple locations for redundancy.
    """
    
    
    # UNIFIED CONFIG INTEGRATION
    from unified_core.config import settings
    STORAGE_LOCATIONS = settings.SCAR_STORAGE_LOCATIONS


    # GPU memory sacrifice per unit of scar depth (in MB)
    # v13.7.2: Reduced from 50.0 to 2.0 to support high scar counts on 12GB GPUs
    SACRIFICE_MB_PER_DEPTH = 2.0
    MAX_GPU_SACRIFICE_PCT = 0.20 # Maximum 20% of GPU memory for scars
    
    def __init__(self, memory=None, world_model=None, enable_enforcement: bool = True):
        self._memory = memory          # CoerciveMemory reference
        self._world_model = world_model  # WorldModel reference
        self._enable_enforcement = enable_enforcement  # True = hard block, False = advisory
        
        self._scars: List[Scar] = []
        self._total_depth: float = 0.0
        self._restricted_actions: Set[str] = set()
        
        # GPU memory sacrifices - NEVER freed per session
        self._sacrificed_tensors: List[tuple] = [] # (tensor, mb)
        self._total_sacrificed_mb: float = 0.0
        self._runtime_sacrificed_mb: float = 0.0 # v2.3: Tracks sacrifice since startup
        self._gpu_available = False
        
        # Hardening v2.1 Metrics
        # Token Bucket for Healing (Max 200MB/min, starts half-full to be conservative)
        self._heal_budget_mb = 100.0
        self._last_heal_time = time.time()
        
        # Create all storage locations
        for loc in self.STORAGE_LOCATIONS:
            os.makedirs(loc, exist_ok=True)
        self._load_state()
        self._check_gpu_availability()
        
        # Apply accumulated pain from previous scars
        self._apply_accumulated_sacrifice()
        
        logger.info(f"ScarTissue initialized: {len(self._scars)} scars, "
                   f"depth={self._total_depth:.2f}, sacrificed={self._total_sacrificed_mb:.1f}MB")
    
    def _check_gpu_availability(self):
        """Check if GPU is available for sacrifice.
        
        v21: DISABLED — GPU sacrifice blocked all Ollama brain calls by
        exhausting VRAM (512MB tensor + 7B model > 12GB). ScarTissue
        tracking continues without GPU penalty. process restart is
        no longer needed to recover VRAM.
        """
        self._gpu_available = False
        logger.info("GPU sacrifice DISABLED (v21) — VRAM reserved for Ollama brain")
    
    def _apply_accumulated_sacrifice(self):
        """Apply GPU sacrifice for all accumulated scars on startup.
        v20: Cap at 512MB to prevent excessive GPU waste on restart.
        """
        if not self._gpu_available or self._total_depth == 0:
            return
        
        # Calculate total sacrifice from accumulated scars
        total_mb = self._total_depth * self.SACRIFICE_MB_PER_DEPTH
        # v20: Cap startup sacrifice — 906 depth * 2.0 MB = 1813MB is too much
        STARTUP_CAP_MB = 512.0
        if total_mb > STARTUP_CAP_MB:
            logger.info(f"Capping startup sacrifice: {total_mb:.1f}MB → {STARTUP_CAP_MB:.1f}MB")
            total_mb = STARTUP_CAP_MB
        self._sacrifice_gpu_memory(total_mb, startup=True)
    
    # Chunk size for GPU sacrifice (prevents heal() from releasing too much at once)
    CHUNK_MB = 50.0
    
    def _sacrifice_gpu_memory(self, mb: float, startup: bool = False):
        """
        Permanently allocate GPU memory in chunks.
        
        THIS MEMORY WILL NEVER BE FREED.
        The only way to recover is to restart the process,
        which will re-apply the sacrifice from persisted scars.
        """
        if not self._gpu_available:
            logger.warning(f"GPU sacrifice requested ({mb:.1f}MB) but GPU not available")
            return
        
        try:
            import torch
            
            # v13.7.2: Safety Cap Enforcement
            total_gpu_mem_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
            max_sac_mb = total_gpu_mem_mb * self.MAX_GPU_SACRIFICE_PCT
            
            if self._total_sacrificed_mb + mb > max_sac_mb:
                original_mb = mb
                mb = max(0.0, max_sac_mb - self._total_sacrificed_mb)
                if mb < 0.1: # Negligible
                     if not startup:
                         logger.warning(f"GPU Sacrifice cap reached ({max_sac_mb:.1f}MB). Skipping additional sacrifice.")
                     return
                logger.info(f"Capping GPU sacrifice: {original_mb:.1f}MB -> {mb:.1f}MB (Hardware Limit)")

            # v2.3.6: Chunked allocation to prevent heal() overshoot
            remaining = mb
            while remaining > 0.0:
                this_mb = min(self.CHUNK_MB, remaining)
                num_elements = int(this_mb * 1024 * 1024 / 4)  # 4 bytes per float32
                t = torch.zeros(num_elements, device='cuda', dtype=torch.float32)
                self._sacrificed_tensors.append((t, this_mb))
                self._total_sacrificed_mb += this_mb
                if not startup:
                    self._runtime_sacrificed_mb += this_mb
                remaining -= this_mb
            
            prefix = "STARTUP SACRIFICE" if startup else "PAIN INFLICTED"
            logger.warning(f"{prefix}: {mb:.1f}MB GPU memory permanently consumed. "
                          f"Total: {self._total_sacrificed_mb:.1f}MB")
            
        except RuntimeError as e:
            # Out of memory - system is critically wounded
            logger.critical(f"GPU SACRIFICE FAILED (OOM): {e}")
        except Exception as e:
            logger.error(f"GPU sacrifice error: {e}")

    
    def _load_state(self):
        """
        Load scars from ALL storage locations.
        Merges scars by scar_id, verifies checksums.
        Uses latest timestamp if duplicates found.
        """
        seen_scar_ids: Dict[str, float] = {}  # scar_id -> created_at
        
        for location in self.STORAGE_LOCATIONS:
            scars_file = os.path.join(location, "scars.jsonl")
            if not os.path.exists(scars_file):
                continue
                
            try:
                with open(scars_file, "r") as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            entry = json.loads(line.strip())
                            
                            # Phase 1: Verify Checksum/Integrity
                            data = self._verify_scar_checksum(entry, scars_file, line_num)
                            if data is None:
                                continue
                            
                            # Phase 2: Process Entry (Deduplication and Object creation)
                            self._process_scar_entry(data, seen_scar_ids)
                            
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON in {scars_file} line {line_num}")
                            
            except Exception as e:
                logger.error(f"Failed to load scars from {location}: {e}")
        
        # Rebuild depth and action mappings
        self._rebuild_remediation_state()
        logger.info(f"Loaded {len(self._scars)} scars from {len(self.STORAGE_LOCATIONS)} locations")

    def _verify_scar_checksum(self, entry: Dict[str, Any], filename: str, line_num: int) -> Optional[Dict[str, Any]]:
        """Verify checksum for an entry or return data for legacy entries."""
        if "checksum" not in entry:
            return entry  # Old format without checksum
            
        data = entry["data"]
        stored_checksum = entry["checksum"]
        computed_checksum = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        
        if stored_checksum != computed_checksum:
            logger.critical(f"⚠️ TAMPERING DETECTED in {filename} line {line_num}!")
            return None
            
        return data

    def _process_scar_entry(self, data: Dict[str, Any], seen_scar_ids: Dict[str, float]):
        """Deduplicate scar by timestamp and instantiate Scar object."""
        scar_id = data["scar_id"]
        created_at = data.get("created_at", 0)
        
        # Skip if we already have a newer version
        if scar_id in seen_scar_ids:
            if created_at <= seen_scar_ids[scar_id]:
                return
        
        seen_scar_ids[scar_id] = created_at
        
        scar = Scar(
            scar_id=scar_id,
            source_failure_id=data["source_failure_id"],
            actions_blocked=data["actions_blocked"],
            beliefs_falsified=data.get("beliefs_falsified", []),
            ideas_penalized=data.get("ideas_penalized", []),
            depth=data.get("depth", 1.0),
            created_at=created_at
        )
        
        # Remove old version if exists and update
        self._scars = [s for s in self._scars if s.scar_id != scar_id]
        self._scars.append(scar)

    def _rebuild_remediation_state(self):
        """Aggregate depth and restricted actions from loaded scars."""
        self._total_depth = sum(s.depth for s in self._scars)
        self._restricted_actions = set()
        for scar in self._scars:
            self._restricted_actions.update(scar.actions_blocked)
    
    def _persist_scar(self, scar: Scar):
        """
        Append scar to ALL storage locations with checksum.
        CANNOT BE UNDONE. Survives deletion of any single location.
        """
        data = scar.to_dict()
        checksum = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        entry = {"data": data, "checksum": checksum}
        entry_json = json.dumps(entry) + "\n"
        
        success_count = 0
        for location in self.STORAGE_LOCATIONS:
            try:
                os.makedirs(location, exist_ok=True)
                scars_file = os.path.join(location, "scars.jsonl")
                with open(scars_file, "a") as f:
                    f.write(entry_json)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to persist scar to {location}: {e}")
        
        if success_count == 0:
            logger.critical(f"SCAR PERSISTENCE FAILED: {scar.scar_id} - NO LOCATIONS AVAILABLE!")
        else:
            logger.warning(f"PERMANENT SCAR RECORDED: {scar.scar_id} to {success_count}/{len(self.STORAGE_LOCATIONS)} locations")
    
    def set_memory(self, memory):
        """Set CoerciveMemory reference."""
        self._memory = memory
    
    def set_world_model(self, world_model):
        """Set WorldModel reference."""
        self._world_model = world_model
    
    async def inflict(self, failure: Failure, severity: str = "medium") -> Optional[Scar]:
        """
        Process failure into permanent scar with Deduplication and Selective Punishment (Async).
        """
        # 0. Deduplication Check
        if self._is_duplicate_failure(failure):
            return next((s for s in self._scars if s.source_failure_id == failure.failure_id), None)

        # 1. Severity Calibration
        severity = self._calibrate_severity(failure, severity)
        is_permanent = (severity != "low")
        is_event = self._is_event(failure)

        # 2. Build Scar Data
        scar_id = hashlib.sha256(f"scar:{failure.failure_id}:{time.time()}".encode()).hexdigest()[:16]
        
        # 3. Apply Penalties
        actions_blocked = self._apply_blocking_logic(failure, is_permanent, is_event, severity)
        beliefs_falsified = await self._apply_falsification_logic(failure, is_permanent)
        ideas_penalized = self._apply_penalization_logic(failure, is_permanent)

        # 4. Record and Persist
        scar = Scar(
            scar_id=scar_id,
            source_failure_id=failure.failure_id,
            actions_blocked=actions_blocked,
            beliefs_falsified=beliefs_falsified,
            ideas_penalized=ideas_penalized,
            depth=self._calculate_scar_depth(severity)
        )
        
        self._scars.append(scar)
        self._total_depth += scar.depth
        self._persist_scar(scar)
        
        # NeuronFabric: Punish neurons associated with failed beliefs
        try:
            from unified_core.core.neuron_fabric import get_neuron_fabric
            fabric = get_neuron_fabric()
            punished = 0
            for belief_id in failure.belief_ids_involved:
                # Find neurons tagged with this belief
                tag = f"bid:{belief_id[:8]}"
                neurons = fabric.get_neurons_by_tag(tag)
                for neuron in neurons:
                    neuron.punish(amount=0.2 * scar.depth)
                    punished += 1
            if punished:
                logger.info(f"🧬 ScarTissue punished {punished} neurons for failure {failure.failure_id[:8]}")
        except Exception as e:
            logger.debug(f"NeuronFabric punishment skipped: {e}")
        
        # 5. GPU Sacrifice
        if severity != "low":
            self._sacrifice_gpu_memory(scar.depth * self.SACRIFICE_MB_PER_DEPTH)
        else:
            logger.info(f"ADVISORY SCAR: {scar_id} recorded without GPU sacrifice.")
        
        if is_permanent and not is_event:
            self._restricted_actions.add(failure.action_type)
            
        return scar

    def _is_duplicate_failure(self, failure: Failure) -> bool:
        """Check if failure has already been processed."""
        return any(s.source_failure_id == failure.failure_id for s in self._scars)

    def _is_event(self, failure: Failure) -> bool:
        """Check if failure is an event rather than an action."""
        return failure.action_type.endswith(("_falsified", "_event"))

    def _calibrate_severity(self, failure: Failure, severity: str) -> str:
        """Adjust severity based on caps and event policy."""
        # Daily Sacrifice Cap Check
        DAILY_CAP_MB = 200.0
        if self._runtime_sacrificed_mb >= DAILY_CAP_MB and severity != "critical":
            logger.warning(f"SCAR CAP REACHED: Quota exceeded. Downgrading to advisory.")
            return "low"

        # Event vs Action Policy
        if self._is_event(failure) and severity != "critical":
            return "low"
            
        return severity

    def _calculate_scar_depth(self, severity: str) -> float:
        """Maps severity to scar depth."""
        mapping = {"critical": 2.0, "medium": 1.0, "low": 0.1}
        return mapping.get(severity, 1.0)

    def _apply_blocking_logic(self, failure: Failure, is_permanent: bool, is_event: bool, severity: str) -> List[str]:
        """Blocks actions in memory if criteria met."""
        if self._memory and is_permanent and not is_event:
            self._memory.block_action(
                pattern=failure.action_type,
                reason=f"Failure scar [{severity}]: {failure.error_message}",
                permanent=True
            )
            return [failure.action_type]
        return []

    async def _apply_falsification_logic(self, failure: Failure, is_permanent: bool) -> List[str]:
        """Falsifies beliefs in WorldModel."""
        falsified = []
        if is_permanent and self._world_model and failure.belief_ids_involved:
            for belief_id in failure.belief_ids_involved:
                await self._world_model.add_belief(
                    f"FALSIFIED: {belief_id} led to {failure.action_type}", 
                    initial_confidence=0.0
                )
                falsified.append(belief_id)
        return falsified

    def _apply_penalization_logic(self, failure: Failure, is_permanent: bool) -> List[str]:
        """Penalizes action keywords in memory."""
        if not self._memory:
            return []
        keywords = failure.action_type.lower().split("_")
        self._memory.penalize_idea(keywords=keywords, base_cost=2.0 if is_permanent else 0.5)
        return keywords

    async def heal(self, success_streak: int = 0, decision_made: bool = True, action_executed: bool = True) -> float:
        """
        Recover sacrificed GPU memory using Refined Exponential Controller (v2.1).
        """
        if not self._gpu_available or not self._sacrificed_tensors:
            return 0.0
            
        if success_streak < 3:
            return 0.0
            
        # 1. Anti-Gaming Rule: No heal credit for idle/failed cycles
        if not decision_made or not action_executed:
            logger.debug("Phantom streak detected (no decision/action). Skipping heal credit.")
            return 0.0

        # 2. Update and Verify Heal Budget
        self._update_heal_budget()
        if self._heal_budget_mb < 50.0:
            return 0.0

        # 3. Calculate recovery amount
        recovered = self._calculate_and_release_recovery(success_streak)
        
        if recovered > 0:
            self._total_sacrificed_mb = max(0.0, self._total_sacrificed_mb - recovered)
            self._heal_budget_mb = max(0.0, self._heal_budget_mb - recovered)
            logger.info(f"💖 REFINED RECOVERY (v2.1): {recovered:.1f}MB released. Streak: {success_streak}")
            
        return recovered

    def _update_heal_budget(self):
        """Replenish Token Bucket for heal rate limiting."""
        now = time.time()
        elapsed = now - self._last_heal_time
        self._heal_budget_mb = min(200.0, self._heal_budget_mb + (elapsed * (200.0 / 60.0)))
        self._last_heal_time = now

    def _calculate_and_release_recovery(self, success_streak: int) -> float:
        """Calculate target MB and release corresponding tensors."""
        # Constants
        SATURATION_CONSTANT = 10.0
        BASE_COEFF = 0.3
        NORM_DEPTH = 5.0
        
        sigma = success_streak / (success_streak + SATURATION_CONSTANT)
        k = BASE_COEFF * min(1.0, self._total_depth / NORM_DEPTH)
        
        target_mb = self._total_sacrificed_mb * k * (1 - math.exp(-sigma))
        target_mb = min(target_mb, self._heal_budget_mb)
        
        # Minimum threshold enforcement
        if target_mb < 50.0:
            if success_streak > 15:
                target_mb = 50.0
            else:
                return 0.0

        recovered = 0.0
        while self._sacrificed_tensors:
            tensor, chunk_mb = self._sacrificed_tensors[-1]
            if recovered + chunk_mb > target_mb:
                break
            self._sacrificed_tensors.pop()
            recovered += chunk_mb
            
        return min(recovered, self._heal_budget_mb)

    
    def get_restricted_actions(self) -> Set[str]:
        """
        Return all actions blocked by scars.
        This set ONLY GROWS, NEVER SHRINKS.
        """
        return self._restricted_actions.copy()
    
    def get_scar_depth(self) -> float:
        """
        Return total accumulated scarring.
        Higher value = more constrained decision space.
        This only increases.
        """
        return self._total_depth
    
    def get_scar_count(self) -> int:
        """Return total scars. This only grows."""
        return len(self._scars)
    
    def is_action_scarred(self, action_type: str) -> bool:
        """Check if action is affected by scarring."""
        return action_type in self._restricted_actions
    
    def is_action_blocked(self, action_type: str) -> bool:
        """
        Check if action is BLOCKED by scarring.
        
        Returns:
            True if:
              - Action is scarred AND enforcement is enabled
            False otherwise (action may proceed, possibly with penalty)
        """
        if not self._enable_enforcement:
            return False  # Advisory mode - not blocked
        return action_type in self._restricted_actions
    
    def get_summary(self) -> Dict[str, Any]:
        """Return scar tissue summary."""
        return {
            "total_scars": len(self._scars),
            "total_depth": self._total_depth,
            "restricted_actions": list(self._restricted_actions),
            "restriction_count": len(self._restricted_actions)
        }


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


class _DeprecatedScarTissue:
    """Deprecated wrapper that warns on instantiation."""
    def __new__(cls, *args, **kwargs):
        return _deprecated_alias("ScarTissue", "FailureRecord", FailureRecord)(*args, **kwargs)


# Backward compatibility alias (with warning)
ScarTissue = _DeprecatedScarTissue
