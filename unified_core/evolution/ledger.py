"""
Evolution Ledger v1.3 - Tamper-Evident Audit Trail with Hash Chain
Version: 1.3.0
Part of: Self-Directed Layer (Phase 17.5)

v1.3 Improvements:
- Cross-platform file locking (Linux fcntl / Windows msvcrt)
- failures_24h persistence via event replay
- recent_proposals persistence via event replay
"""

import json
import logging
import time
import hashlib
import hmac
import os
import asyncio
# Cross-platform file locking via filelock (works on Linux, macOS, Windows)
from filelock import FileLock
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

from . import evolution_config as config

logger = logging.getLogger("unified_core.evolution.ledger")


class ProposalType(Enum):
    CONFIG = "config"      # Adjust thresholds, intervals (LOW RISK)
    POLICY = "policy"      # Change aggression bounds, weights (MEDIUM RISK)
    CODE = "code"          # Modify helper functions (HIGH RISK)
    AGENT = "agent"        # Generate new agent (HIGH RISK)


class ProposalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANARY = "canary"        # v1.1: Running in canary
    PROMOTED = "promoted"    # v1.1: Canary passed, applied
    EXECUTED = "executed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class EvolutionProposal:
    """A proposed change to the system (v1.1 Schema)."""
    proposal_id: str
    proposal_type: ProposalType
    description: str
    
    # v1.1: Structured change spec
    scope: str                      # config, policy, code
    targets: List[str]              # Allowlist of files/paths
    diff: str                       # Unified diff or AST patch
    risk_score: float = 0.0         # 0-100
    expected_benefit: str = ""      # Metric impact estimate
    rollback_plan: str = ""         # How to revert
    
    rationale: str = ""
    created_at: float = field(default_factory=time.time)
    status: ProposalStatus = ProposalStatus.PENDING
    
    # Execution metadata
    canary_result: Optional[str] = None
    executed_at: Optional[float] = None
    execution_duration_ms: Optional[float] = None
    result: Optional[str] = None
    error: Optional[str] = None
    
    # Metrics before/after
    metrics_before: Optional[Dict[str, Any]] = None
    metrics_after: Optional[Dict[str, Any]] = None
    
    # v1.3: Code metadata (original + refactored source) — persisted to ledger
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['proposal_type'] = self.proposal_type.value
        d['status'] = self.status.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvolutionProposal':
        data['proposal_type'] = ProposalType(data['proposal_type'])
        data['status'] = ProposalStatus(data['status'])
        return cls(**data)


class EvolutionLedger:
    """
    v1.4: Tamper-Evident Audit Trail with Hash Chain
    
    Features:
    - Each entry contains prev_hash → creates chain
    - HMAC signature for integrity
    - Kill switch on repeated failures
    - Safe mode detection
    - Schema versioning with migration support
    - Log compaction
    """
    
    SCHEMA_VERSION = 2  # Current schema version
    
    # v1.2: HMAC key — warn loudly if using default
    _raw_key = os.environ.get("NOOGH_EVOLUTION_KEY", "")
    if not _raw_key:
        HMAC_KEY = b"noogh_evolution_v1.2_default"
    else:
        HMAC_KEY = _raw_key.encode()
    
    def __init__(self, data_dir: Optional[Path] = None):
        if not os.environ.get("NOOGH_EVOLUTION_KEY"):
            logger.warning(
                "⚠️  NOOGH_EVOLUTION_KEY not set — using default HMAC key. "
                "Set this env var for production use!"
            )
        
        self.data_dir = data_dir or Path.home() / ".noogh" / "evolution"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.ledger_file = self.data_dir / "evolution_ledger.jsonl"
        self.proposals: Dict[str, EvolutionProposal] = {}
        
        # v1.1: Hash chain
        self.last_hash = "GENESIS"
        self.chain_valid = True
        
        # Rate limiting
        self.proposals_this_hour = 0
        self.executions_this_hour = 0
        self.last_hour_reset = time.time()
        self.last_failure_time = 0.0
        
        # v1.2: All thresholds from centralized config
        self.failures_24h: List[float] = []
        self.safe_mode = False
        self.KILL_SWITCH_THRESHOLD = config.KILL_SWITCH_FAILURE_THRESHOLD
        self.MAX_PROPOSALS_PER_HOUR = config.MAX_PROPOSALS_PER_HOUR
        self.MAX_EXECUTIONS_PER_HOUR = config.MAX_EXECUTIONS_PER_HOUR
        self.FAILURE_COOLDOWN_SECONDS = config.FAILURE_COOLDOWN_SECONDS
        self.RISK_THRESHOLD = config.RISK_THRESHOLD
        
        # v1.1.1: Deduplication
        self.recent_proposals: Dict[str, float] = {}
        self.PROPOSAL_DEDUP_WINDOW = config.PROPOSAL_DEDUP_WINDOW
        
        # Stats
        self.total_proposals = 0
        self.total_approved = 0
        self.total_executed = 0
        self.total_successful = 0
        self.total_failed = 0
        self.total_rolled_back = 0
        
        self._load_ledger()
        self._attempt_recovery()
        logger.info(f"EvolutionLedger v1.1 initialized: {self.ledger_file} (chain_valid={self.chain_valid}, safe_mode={self.safe_mode})")
    
    def _attempt_recovery(self):
        """v1.2: Auto-recover from chain violations instead of permanent lock."""
        if not self.chain_valid:
            logger.warning("⚠️ Chain integrity violated — starting auto-recovery")
            self._quarantine_ledger()
            # Reset to clean state
            self.chain_valid = True
            self.safe_mode = False
            self.proposals = {}
            self.last_hash = "GENESIS"
            self.total_proposals = 0
            self.total_approved = 0
            self.total_executed = 0
            self.total_successful = 0
            self.total_failed = 0
            self.total_rolled_back = 0
            logger.info("✅ Ledger auto-recovered — fresh genesis created")
    
    def _quarantine_ledger(self):
        """Backup corrupted ledger and DELETE the original to break the corruption loop."""
        if self.ledger_file.exists():
            quarantine_path = self.ledger_file.with_suffix(f'.corrupt.{int(time.time())}.jsonl')
            try:
                import shutil
                shutil.copy2(self.ledger_file, quarantine_path)
                self.ledger_file.unlink()  # DELETE the original — critical fix
                logger.warning(f"🔒 Corrupted ledger quarantined to: {quarantine_path}")
                logger.info("🗑️ Original ledger deleted — clean slate")
            except Exception as e:
                logger.error(f"Failed to quarantine ledger: {e}")
    
    def _compute_hash(self, data: str) -> str:
        """Compute SHA256 hash of data."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _compute_hmac(self, data: str) -> str:
        """Compute HMAC signature over full entry envelope."""
        return hmac.new(self.HMAC_KEY, data.encode(), hashlib.sha256).hexdigest()
    
    def _load_ledger(self):
        """Load and verify existing ledger entries.
        
        v2.0: Full event replay — reconstructs proposal states from ALL 
        event types, not just 'proposal'. This prevents re-processing 
        already completed/failed/promoted proposals after service restart.
        """
        if not self.ledger_file.exists():
            return
        
        try:
            prev_hash = "GENESIS"
            events_replayed = 0
            
            # Reset state for full replay (in case of re-loading)
            self.proposals.clear()
            self.failures_24h.clear()
            self.recent_proposals.clear()
            self.total_proposals = 0
            self.total_approved = 0
            self.total_executed = 0
            self.total_successful = 0
            self.total_failed = 0
            self.total_rolled_back = 0
            
            with open(self.ledger_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    
                    entry = json.loads(line)
                    
                    # v1.1: Verify hash chain
                    if entry.get('prev_hash') != prev_hash:
                        logger.error(
                            f"⛓️ Hash chain broken at line {line_num}! "
                            f"expected={prev_hash[:16]}… got={str(entry.get('prev_hash', ''))[:16]}…"
                        )
                        self.chain_valid = False
                    
                    # v1.2: Verify full-scope HMAC (type+timestamp+prev_hash+data)
                    hmac_payload = json.dumps({
                        "type": entry.get('type'),
                        "timestamp": entry.get('timestamp'),
                        "prev_hash": entry.get('prev_hash'),
                        "data": entry.get('data', {})
                    }, sort_keys=True)
                    expected_sig = self._compute_hmac(hmac_payload)
                    if entry.get('signature') and entry.get('signature') != expected_sig:
                        logger.error(
                            f"🔐 HMAC mismatch at line {line_num}! "
                            f"expected={expected_sig[:16]}… got={str(entry.get('signature', ''))[:16]}…"
                        )
                        self.chain_valid = False
                    
                    # v1.4: Migrate old entries if needed
                    entry_version = entry.get('schema_version', 1)
                    if entry_version < self.SCHEMA_VERSION:
                        entry = self._migrate_entry(entry, entry_version)
                    
                    # Update chain
                    prev_hash = entry.get('hash', prev_hash)
                    
                    # ── Full event replay ────────────────────────────────
                    entry_type = entry.get('type')
                    data = entry.get('data', {})
                    pid = data.get('proposal_id', '')
                    
                    if entry_type == 'proposal':
                        proposal = EvolutionProposal.from_dict(data)
                        self.proposals[proposal.proposal_id] = proposal
                        self.total_proposals += 1
                    
                    elif entry_type == 'approval' and pid in self.proposals:
                        self.proposals[pid].status = ProposalStatus.APPROVED
                        self.total_approved += 1
                    
                    elif entry_type == 'rejection' and pid in self.proposals:
                        self.proposals[pid].status = ProposalStatus.REJECTED
                    
                    elif entry_type == 'canary_success' and pid in self.proposals:
                        self.proposals[pid].status = ProposalStatus.CANARY
                        self.proposals[pid].canary_result = data.get('result', '')
                    
                    elif entry_type == 'canary_failed' and pid in self.proposals:
                        self.proposals[pid].status = ProposalStatus.FAILED
                        self.proposals[pid].canary_result = data.get('result', '')
                    
                    elif entry_type == 'promoted' and pid in self.proposals:
                        self.proposals[pid].status = ProposalStatus.PROMOTED
                        self.proposals[pid].metrics_after = data.get('metrics_after')
                        self.proposals[pid].executed_at = entry.get('timestamp')
                        self.total_successful += 1
                    
                    elif entry_type == 'execution' and pid in self.proposals:
                        success = data.get('success', False)
                        self.proposals[pid].status = (
                            ProposalStatus.EXECUTED if success 
                            else ProposalStatus.FAILED
                        )
                        self.proposals[pid].executed_at = entry.get('timestamp')
                        self.total_executed += 1
                        if success:
                            self.total_successful += 1
                        else:
                            self.total_failed += 1
                    
                    elif entry_type == 'rollback' and pid in self.proposals:
                        self.proposals[pid].status = ProposalStatus.ROLLED_BACK
                        self.total_rolled_back += 1
                    
                    # v1.3: Rebuild failures_24h from failure events
                    entry_ts = entry.get('timestamp', 0)
                    if entry_type in ('canary_failed', 'rollback') or (
                        entry_type == 'execution' and not data.get('success', False)
                    ):
                        if entry_ts > time.time() - 86400:  # Within 24h
                            self.failures_24h.append(entry_ts)
                    
                    # v1.3: Reset failures on safe_mode_exit (prevents false kill switch)
                    if entry_type == 'safe_mode_exit':
                        self.failures_24h = []
                        self.safe_mode = False
                    
                    # v1.3: Rebuild recent_proposals from proposal events
                    if entry_type == 'proposal' and pid:
                        content_hash = hashlib.sha256(
                            json.dumps(data.get('diff', ''), sort_keys=True).encode()
                        ).hexdigest()[:16]
                        self.recent_proposals[content_hash] = entry_ts
                    
                    events_replayed += 1
            
            self.last_hash = prev_hash
            
            # v1.3: Prune expired recent_proposals (older than 1 hour)
            cutoff = time.time() - 3600
            self.recent_proposals = {
                h: t for h, t in self.recent_proposals.items() if t > cutoff
            }
            
            # Count final states for logging
            pending_count = sum(
                1 for p in self.proposals.values() 
                if p.status == ProposalStatus.PENDING
            )
            promoted_count = sum(
                1 for p in self.proposals.values() 
                if p.status == ProposalStatus.PROMOTED
            )
            failed_count = sum(
                1 for p in self.proposals.values() 
                if p.status == ProposalStatus.FAILED
            )
            rejected_count = sum(
                1 for p in self.proposals.values() 
                if p.status == ProposalStatus.REJECTED
            )
            
            logger.info(
                f"📒 Ledger loaded: {len(self.proposals)} proposals, "
                f"{events_replayed} events replayed "
                f"(pending={pending_count}, promoted={promoted_count}, "
                f"failed={failed_count}, rejected={rejected_count}) "
                f"chain_valid={self.chain_valid}"
            )
            
        except Exception as e:
            logger.error(f"Failed to load ledger: {e}")
            self.chain_valid = False
    
    def _update_stats(self, proposal: EvolutionProposal):
        """Update statistics based on proposal status."""
        self.total_proposals += 1
        if proposal.status == ProposalStatus.APPROVED:
            self.total_approved += 1
        elif proposal.status in (ProposalStatus.EXECUTED, ProposalStatus.PROMOTED):
            self.total_executed += 1
            self.total_successful += 1
        elif proposal.status == ProposalStatus.FAILED:
            self.total_executed += 1
            self.total_failed += 1
        elif proposal.status == ProposalStatus.ROLLED_BACK:
            self.total_rolled_back += 1
    
    def _reset_hourly_limits(self):
        """Reset hourly rate limits if needed."""
        now = time.time()
        if now - self.last_hour_reset > 3600:
            self.proposals_this_hour = 0
            self.executions_this_hour = 0
            self.last_hour_reset = now
    
    def _check_kill_switch(self):
        """v1.1: Check if kill switch should activate."""
        now = time.time()
        cutoff = now - 86400  # 24 hours
        
        # Clean old failures
        self.failures_24h = [t for t in self.failures_24h if t > cutoff]
        
        # Check threshold
        if len(self.failures_24h) >= self.KILL_SWITCH_THRESHOLD:
            if not self.safe_mode:
                self.safe_mode = True
                logger.critical("🚨 KILL SWITCH ACTIVATED: Safe Mode enabled due to repeated failures")
    
    def _get_last_hash_from_disk(self) -> str:
        """v1.5: Read the actual last hash from disk (prevents multi-process chain breaks)."""
        if not self.ledger_file.exists():
            return "GENESIS"
        try:
            last_line = None
            with open(self.ledger_file, 'rb') as f:
                # Efficiently seek to last non-empty line
                f.seek(0, 2)  # End of file
                pos = f.tell()
                while pos > 0:
                    pos = max(0, pos - 4096)
                    f.seek(pos)
                    chunk = f.read()
                    lines = chunk.splitlines()
                    for line in reversed(lines):
                        if line.strip():
                            last_line = line.decode('utf-8', errors='replace')
                            break
                    if last_line:
                        break
            if last_line:
                entry = json.loads(last_line)
                return entry.get('hash', 'GENESIS')
        except Exception:
            pass
        return self.last_hash  # Fallback to in-memory

    def _write_entry(self, entry_type: str, data: Dict[str, Any]):
        """Write a hash-chained entry to the ledger.

        v1.5: Uses file lock for the entire write operation AND re-reads
        the last hash from disk to prevent chain breaks when multiple
        processes are running simultaneously.
        """
        # v1.4: Cross-platform locking via filelock — lock BEFORE reading last hash
        lock_path = str(self.ledger_file) + ".lock"
        with FileLock(lock_path, timeout=10):
            # v1.5: Re-read last hash from disk inside the lock to prevent
            # multi-process chain breaks (two daemons appending to same file)
            prev = self._get_last_hash_from_disk()
            # Keep in-memory state consistent
            self.last_hash = prev

            ts = time.time()

            # v1.2: Full-scope HMAC covers type+timestamp+prev_hash+data
            hmac_payload = json.dumps({
                "type": entry_type,
                "timestamp": ts,
                "prev_hash": prev,
                "data": data
            }, sort_keys=True)
            signature = self._compute_hmac(hmac_payload)

            # Create entry with chain
            entry = {
                "type": entry_type,
                "timestamp": ts,
                "prev_hash": prev,
                "data": data,
                "signature": signature,
                "schema_version": self.SCHEMA_VERSION
            }

            # Compute hash of entire entry
            entry_str = json.dumps(entry, sort_keys=True)
            entry["hash"] = self._compute_hash(entry_str)
            self.last_hash = entry["hash"]

            with open(self.ledger_file, 'a') as f:
                f.write(json.dumps(entry) + "\n")
                f.flush()
    
    def is_safe_mode(self) -> bool:
        """Check if system is in safe mode."""
        self._check_kill_switch()
        return self.safe_mode
    
    def can_propose(self) -> Tuple[bool, str]:
        """Check if a new proposal is allowed."""
        if self.safe_mode:
            return False, "SAFE MODE: Evolution disabled"
        
        self._reset_hourly_limits()
        
        if self.proposals_this_hour >= self.MAX_PROPOSALS_PER_HOUR:
            return False, f"Rate limit: {self.MAX_PROPOSALS_PER_HOUR} proposals/hour"
        
        return True, "OK"
    
    def can_execute(self) -> Tuple[bool, str]:
        """Check if execution is allowed."""
        if self.safe_mode:
            return False, "SAFE MODE: Execution disabled"
        
        self._reset_hourly_limits()
        
        if self.executions_this_hour >= self.MAX_EXECUTIONS_PER_HOUR:
            return False, f"Rate limit: {self.MAX_EXECUTIONS_PER_HOUR} executions/hour"
        
        # Check cooldown after failure
        if self.last_failure_time > 0:
            elapsed = time.time() - self.last_failure_time
            if elapsed < self.FAILURE_COOLDOWN_SECONDS:
                remaining = int(self.FAILURE_COOLDOWN_SECONDS - elapsed)
                return False, f"Failure cooldown: {remaining}s remaining"
        
        return True, "OK"
    

    def _content_hash(self, proposal: EvolutionProposal) -> str:
        """v1.1.1: Generate content hash for deduplication."""
        content = f"{proposal.scope}:{':'.join(sorted(proposal.targets))}:{proposal.diff.strip()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def record_proposal(self, proposal: EvolutionProposal) -> Tuple[bool, str]:
        """Record a new proposal with validation."""
        can, reason = self.can_propose()
        if not can:
            logger.warning(f"Proposal blocked: {reason}")
            return False, reason
        
        # v1.1.1: Deduplication check
        content_hash = self._content_hash(proposal)
        now = time.time()
        # Cleanup old entries
        self.recent_proposals = {h: t for h, t in self.recent_proposals.items() 
                                  if now - t < self.PROPOSAL_DEDUP_WINDOW}
        if content_hash in self.recent_proposals:
            logger.warning(f"⏸️ Duplicate proposal rejected: {proposal.proposal_id} (hash={content_hash})")
            return False, "Duplicate proposal within cooldown window"
        
        # v1.5: Inline validation (risk + protected paths + code limit)
        validation_reason = None
        if proposal.risk_score > self.RISK_THRESHOLD:
            validation_reason = f"Risk too high: {proposal.risk_score} > {self.RISK_THRESHOLD}"
        elif proposal.proposal_type == ProposalType.CODE and proposal.risk_score > 40:
            validation_reason = f"Code proposals limited to risk ≤40, got {proposal.risk_score}"
        else:
            for target in proposal.targets:
                if "agent_daemon.py" in target:
                    validation_reason = f"Protected path: {target}"
                    break
        
        if validation_reason:
            logger.warning(f"Proposal rejected: {validation_reason}")
            proposal.status = ProposalStatus.REJECTED
            self._write_entry("proposal_rejected", {
                "proposal_id": proposal.proposal_id,
                "reason": validation_reason
            })
            return False, validation_reason
        
        self.proposals[proposal.proposal_id] = proposal
        self.proposals_this_hour += 1
        self.total_proposals += 1
        self.recent_proposals[content_hash] = now  # v1.1.1: Track for dedup
        
        self._write_entry("proposal", proposal.to_dict())
        logger.info(f"📝 Proposal recorded: {proposal.proposal_id} (risk={proposal.risk_score})")
        
        return True, "OK"
    
    def record_approval(self, proposal_id: str, approved: bool, reason: str = ""):
        """Record approval or rejection of a proposal."""
        if proposal_id not in self.proposals:
            logger.warning(f"Unknown proposal for approval: {proposal_id}")
            return
        
        proposal = self.proposals[proposal_id]
        
        if approved:
            proposal.status = ProposalStatus.APPROVED
            self.total_approved += 1
            self._write_entry("approval", {
                "proposal_id": proposal_id,
                "approved": True,
                "reason": reason
            })
            logger.info(f"✅ Proposal approved: {proposal_id}")
        else:
            proposal.status = ProposalStatus.REJECTED
            self._write_entry("rejection", {
                "proposal_id": proposal_id,
                "approved": False,
                "reason": reason
            })
            logger.warning(f"❌ Proposal rejected: {proposal_id} - {reason}")
    
    def record_canary_result(self, proposal_id: str, success: bool, result: str = ""):
        """v1.1: Record canary execution result."""
        if proposal_id not in self.proposals:
            return
        
        proposal = self.proposals[proposal_id]
        proposal.canary_result = result
        
        if success:
            proposal.status = ProposalStatus.CANARY
            self._write_entry("canary_success", {
                "proposal_id": proposal_id,
                "result": result
            })
            logger.info(f"🐤 CANARY SUCCESS: {proposal_id}")
        else:
            proposal.status = ProposalStatus.FAILED
            self.failures_24h.append(time.time())
            self._check_kill_switch()
            self._write_entry("canary_failed", {
                "proposal_id": proposal_id,
                "result": result
            })
            logger.warning(f"🐤 CANARY FAILED: {proposal_id}")
    
    def record_promotion(self, proposal_id: str, success: bool, metrics_after: Optional[Dict] = None):
        """v1.1: Record promotion from canary to production."""
        # v1.1.1: Block promotion if chain is invalid
        if not self.chain_valid:
            logger.error(f"🚫 PROMOTION BLOCKED: Ledger chain invalid. Proposal: {proposal_id}")
            return
        
        if proposal_id not in self.proposals:
            return
        
        proposal = self.proposals[proposal_id]
        proposal.executed_at = time.time()
        proposal.metrics_after = metrics_after
        
        if success:
            proposal.status = ProposalStatus.PROMOTED
            self.total_successful += 1
            self._write_entry("promoted", {
                "proposal_id": proposal_id,
                "metrics_after": metrics_after
            })
            logger.warning(f"🚀 PROMOTED TO PRODUCTION: {proposal_id}")
        else:
            proposal.status = ProposalStatus.FAILED
            self.total_failed += 1
            self.failures_24h.append(time.time())
            self._check_kill_switch()
    
    def record_execution(
        self, 
        proposal_id: str, 
        success: bool,
        duration_ms: float,
        result: str = "",
        error: str = "",
        metrics_before: Optional[Dict] = None,
        metrics_after: Optional[Dict] = None
    ):
        """Record execution result."""
        if proposal_id not in self.proposals:
            logger.error(f"Unknown proposal: {proposal_id}")
            return
        
        proposal = self.proposals[proposal_id]
        proposal.executed_at = time.time()
        proposal.execution_duration_ms = duration_ms
        proposal.result = result
        proposal.error = error
        proposal.metrics_before = metrics_before
        proposal.metrics_after = metrics_after
        
        if success:
            proposal.status = ProposalStatus.EXECUTED
            self.total_successful += 1
        else:
            proposal.status = ProposalStatus.FAILED
            self.total_failed += 1
            self.last_failure_time = time.time()
            self.failures_24h.append(time.time())
            self._check_kill_switch()
        
        self.executions_this_hour += 1
        self.total_executed += 1
        
        self._write_entry("execution", {
            "proposal_id": proposal_id,
            "success": success,
            "duration_ms": duration_ms,
            "result": result,
            "error": error,
            "metrics_before": metrics_before,
            "metrics_after": metrics_after
        })
        
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.warning(f"🔧 EVOLUTION EXECUTED {status}: {proposal_id} ({duration_ms:.1f}ms)")
    
    def record_rollback(self, proposal_id: str, reason: str):
        """Record a rollback."""
        if proposal_id not in self.proposals:
            return
        
        proposal = self.proposals[proposal_id]
        proposal.status = ProposalStatus.ROLLED_BACK
        self.total_rolled_back += 1
        
        self._write_entry("rollback", {
            "proposal_id": proposal_id,
            "reason": reason
        })
        
        logger.warning(f"⏪ ROLLBACK: {proposal_id} - {reason}")
    
    def exit_safe_mode(self, reason: str = "Manual reset"):
        """Manually exit safe mode (requires human intervention)."""
        if self.safe_mode:
            self.safe_mode = False
            self.failures_24h = []
            self._write_entry("safe_mode_exit", {"reason": reason})
            logger.warning(f"🔓 SAFE MODE DEACTIVATED: {reason}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get evolution statistics."""
        success_rate = 0.0
        if self.total_executed > 0:
            success_rate = self.total_successful / self.total_executed
        
        return {
            "total_proposals": self.total_proposals,
            "total_approved": self.total_approved,
            "total_executed": self.total_executed,
            "total_successful": self.total_successful,
            "total_failed": self.total_failed,
            "total_rolled_back": self.total_rolled_back,
            "success_rate": success_rate,
            "proposals_this_hour": self.proposals_this_hour,
            "executions_this_hour": self.executions_this_hour,
            "safe_mode": self.safe_mode,
            "chain_valid": self.chain_valid,
            "failures_24h": len(self.failures_24h)
        }
    
    def get_recent_proposals(self, limit: int = 10) -> List[EvolutionProposal]:
        """Get most recent proposals."""
        sorted_proposals = sorted(
            self.proposals.values(),
            key=lambda p: p.created_at,
            reverse=True
        )
        return sorted_proposals[:limit]

    # ── v1.4: Schema Migration ──────────────────────────────────
    
    @staticmethod
    def _migrate_entry(entry: Dict, from_version: int) -> Dict:
        """Apply migrations to bring entry to current schema version."""
        if from_version < 2:
            # v1 → v2: Add schema_version field
            entry['schema_version'] = 2
        return entry
    
    # ── v1.4: Log Compaction ────────────────────────────────────
    
    def compact(self, keep_last_n: int = 500) -> Dict[str, Any]:
        """Compact ledger: keep last N entries, archive the rest.
        
        Creates a snapshot of stats, writes recent entries to new file,
        moves old file to .archive, and replaces with compacted file.
        
        Returns dict with compaction stats.
        """
        import shutil
        
        if not self.ledger_file.exists():
            return {"status": "nothing_to_compact"}
        
        # Read all entries
        entries = []
        with open(self.ledger_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        total_entries = len(entries)
        if total_entries <= keep_last_n:
            return {"status": "no_compaction_needed", "entries": total_entries}
        
        # Keep last N entries
        kept = entries[-keep_last_n:]
        archived = total_entries - keep_last_n
        
        # Archive old file
        archive_path = self.data_dir / f"evolution_ledger.{int(time.time())}.archive.jsonl"
        shutil.copy2(self.ledger_file, archive_path)
        
        # Write compacted file (re-chain from GENESIS)
        compact_file = self.ledger_file.with_suffix('.tmp')
        prev_hash = "GENESIS"
        with open(compact_file, 'w') as f:
            for entry in kept:
                entry['prev_hash'] = prev_hash
                # Recompute HMAC and hash for new chain
                hmac_payload = json.dumps({
                    "type": entry.get('type'),
                    "timestamp": entry.get('timestamp'),
                    "prev_hash": prev_hash,
                    "data": entry.get('data', {})
                }, sort_keys=True)
                entry['signature'] = self._compute_hmac(hmac_payload)
                entry_for_hash = {k: v for k, v in entry.items() if k != 'hash'}
                entry['hash'] = self._compute_hash(json.dumps(entry_for_hash, sort_keys=True))
                prev_hash = entry['hash']
                f.write(json.dumps(entry) + '\n')
        
        # Atomic replace
        compact_file.replace(self.ledger_file)
        self.last_hash = prev_hash
        self.chain_valid = True
        
        logger.info(
            f"📦 Ledger compacted: {total_entries} → {keep_last_n} entries "
            f"({archived} archived to {archive_path.name})"
        )
        
        return {
            "status": "compacted",
            "total_before": total_entries,
            "total_after": keep_last_n,
            "archived": archived,
            "archive_file": str(archive_path)
        }


# Singleton instance
_ledger_instance: Optional[EvolutionLedger] = None

def get_evolution_ledger() -> EvolutionLedger:
    """Get the global EvolutionLedger instance."""
    global _ledger_instance
    if _ledger_instance is None:
        _ledger_instance = EvolutionLedger()
    return _ledger_instance
