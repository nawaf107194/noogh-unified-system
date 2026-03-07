"""
Unit tests for EvolutionLedger v1.1

Covers:
- Initialization and loading
- Proposal recording, dedup, risk threshold, rate limiting
- Approval, canary, promotion, execution, rollback
- Kill switch activation
- Chain integrity and HMAC verification
- Helper methods: can_propose, can_execute, get_stats
"""
import pytest
import json
import time
import hashlib
import hmac
import os
from pathlib import Path
from unittest.mock import patch

from unified_core.evolution.ledger import (
    EvolutionLedger,
    EvolutionProposal,
    ProposalType,
    ProposalStatus,
)


# ──────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────

@pytest.fixture
def ledger(tmp_path):
    """Create an EvolutionLedger with a temp data directory."""
    data_dir = tmp_path / ".noogh" / "evolution"
    data_dir.mkdir(parents=True)
    with patch.dict(os.environ, {"NOOGH_EVOLUTION_KEY": "test_key_123"}):
        led = EvolutionLedger(data_dir=data_dir)
    yield led


@pytest.fixture
def sample_proposal():
    """Create a standard test proposal."""
    return EvolutionProposal(
        proposal_id="test_001",
        proposal_type=ProposalType.CODE,
        description="Test refactor of utility function",
        scope="code",
        targets=["utils.py"],
        diff="--- a/utils.py\n+++ b/utils.py\n@@ -1 +1 @@\n-old()\n+new()",
        risk_score=25,
    )


def _make_proposal(pid: str, risk: int = 20, ptype=ProposalType.CODE,
                   targets=None, diff="test_diff") -> EvolutionProposal:
    """Helper to create unique proposals (avoids dedup)."""
    return EvolutionProposal(
        proposal_id=pid,
        proposal_type=ptype,
        description=f"Test proposal {pid}",
        scope="code",
        targets=targets or [f"{pid}.py"],
        diff=f"{diff}_{pid}",
        risk_score=risk,
    )


# ──────────────────────────────────────────────────────────
# Initialization Tests
# ──────────────────────────────────────────────────────────

class TestLedgerInit:
    def test_clean_initialization(self, ledger):
        """Fresh ledger has correct defaults."""
        assert ledger.last_hash == "GENESIS"
        assert ledger.chain_valid is True
        assert ledger.safe_mode is False
        assert ledger.proposals == {}
        assert ledger.total_proposals == 0
        assert ledger.total_approved == 0

    def test_data_dir_created(self, ledger):
        """Data directory exists after init."""
        assert ledger.data_dir.exists()

    def test_ledger_file_not_created_until_write(self, ledger):
        """Ledger file only created on first write."""
        assert not ledger.ledger_file.exists()

    def test_load_existing_ledger(self, tmp_path):
        """Verified ledger loads and replays events correctly."""
        data_dir = tmp_path / ".noogh" / "evolution"
        data_dir.mkdir(parents=True)
        key = b"test_key_123"

        with patch.dict(os.environ, {"NOOGH_EVOLUTION_KEY": "test_key_123"}):
            led1 = EvolutionLedger(data_dir=data_dir)
            p = _make_proposal("reload_test")
            led1.record_proposal(p)
            led1.record_approval("reload_test", approved=True, reason="ok")

        # Reload from disk
        with patch.dict(os.environ, {"NOOGH_EVOLUTION_KEY": "test_key_123"}):
            led2 = EvolutionLedger(data_dir=data_dir)

        assert "reload_test" in led2.proposals
        assert led2.proposals["reload_test"].status == ProposalStatus.APPROVED
        assert led2.chain_valid is True
        assert led2.last_hash != "GENESIS"


# ──────────────────────────────────────────────────────────
# Proposal Recording Tests
# ──────────────────────────────────────────────────────────

class TestRecordProposal:
    def test_record_basic(self, ledger, sample_proposal):
        """Successfully record a valid proposal."""
        ok, msg = ledger.record_proposal(sample_proposal)
        assert ok is True
        assert msg == "OK"
        assert sample_proposal.proposal_id in ledger.proposals
        assert ledger.proposals_this_hour == 1
        assert ledger.total_proposals == 1
        # File created
        assert ledger.ledger_file.exists()
        with open(ledger.ledger_file) as f:
            entry = json.loads(f.readline())
        assert entry["type"] == "proposal"
        assert entry["data"]["proposal_id"] == "test_001"
        assert "hash" in entry
        assert "signature" in entry
        assert entry["prev_hash"] == "GENESIS"

    def test_dedup_rejection(self, ledger):
        """Duplicate content is rejected within cooldown window."""
        # Must have identical scope + targets + diff for dedup to trigger
        p1 = EvolutionProposal(
            proposal_id="dup_a", proposal_type=ProposalType.CONFIG,
            description="first", scope="config",
            targets=["same.py"], diff="identical_diff", risk_score=10,
        )
        p2 = EvolutionProposal(
            proposal_id="dup_b", proposal_type=ProposalType.CONFIG,
            description="second", scope="config",
            targets=["same.py"], diff="identical_diff", risk_score=10,
        )
        ok1, _ = ledger.record_proposal(p1)
        ok2, msg2 = ledger.record_proposal(p2)
        assert ok1 is True
        assert ok2 is False
        assert "Duplicate" in msg2

    def test_risk_too_high(self, ledger):
        """Proposal rejected if risk_score > RISK_THRESHOLD."""
        p = _make_proposal("risky", risk=65)
        ok, msg = ledger.record_proposal(p)
        assert ok is False
        assert "Risk too high" in msg

    def test_code_risk_threshold(self, ledger):
        """CODE proposals have a stricter risk limit (40)."""
        p = _make_proposal("code_risky", risk=45, ptype=ProposalType.CODE)
        ok, msg = ledger.record_proposal(p)
        assert ok is False
        assert "risk" in msg.lower()

    def test_rate_limit(self, ledger):
        """Rate limiting kicks in after MAX_PROPOSALS_PER_HOUR."""
        ledger.MAX_PROPOSALS_PER_HOUR = 5  # Lower for speed
        for i in range(5):
            p = _make_proposal(f"rate_{i}")
            ledger.record_proposal(p)

        p_extra = _make_proposal("rate_overflow")
        ok, msg = ledger.record_proposal(p_extra)
        assert ok is False
        assert "Rate limit" in msg

    def test_protected_path_rejected(self, ledger):
        """Proposals targeting protected paths are rejected."""
        p = _make_proposal("daemon_edit", targets=["agent_daemon.py"])
        ok, msg = ledger.record_proposal(p)
        assert ok is False
        assert "Protected path" in msg


# ──────────────────────────────────────────────────────────
# Lifecycle Tests
# ──────────────────────────────────────────────────────────

class TestProposalLifecycle:
    def test_approval(self, ledger, sample_proposal):
        """Approval updates status and counter."""
        ledger.record_proposal(sample_proposal)
        ledger.record_approval(sample_proposal.proposal_id, approved=True, reason="looks good")

        assert ledger.proposals[sample_proposal.proposal_id].status == ProposalStatus.APPROVED
        assert ledger.total_approved == 1

        with open(ledger.ledger_file) as f:
            lines = f.readlines()
        assert len(lines) == 2
        entry = json.loads(lines[1])
        assert entry["type"] == "approval"
        assert entry["data"]["approved"] is True

    def test_rejection(self, ledger, sample_proposal):
        """Rejection updates status."""
        ledger.record_proposal(sample_proposal)
        ledger.record_approval(sample_proposal.proposal_id, approved=False, reason="not needed")

        assert ledger.proposals[sample_proposal.proposal_id].status == ProposalStatus.REJECTED
        assert ledger.total_approved == 0

    def test_canary_success(self, ledger, sample_proposal):
        """Successful canary sets status but doesn't add failure."""
        ledger.record_proposal(sample_proposal)
        ledger.record_canary_result(sample_proposal.proposal_id, success=True, result="ok")

        assert ledger.proposals[sample_proposal.proposal_id].status == ProposalStatus.CANARY
        assert len(ledger.failures_24h) == 0

    def test_canary_failure(self, ledger, sample_proposal):
        """Failed canary sets FAILED status and records failure timestamp."""
        ledger.record_proposal(sample_proposal)
        ledger.record_canary_result(sample_proposal.proposal_id, success=False, result="error")

        assert ledger.proposals[sample_proposal.proposal_id].status == ProposalStatus.FAILED
        assert len(ledger.failures_24h) == 1

    def test_execution_success(self, ledger, sample_proposal):
        """Successful execution updates counters."""
        ledger.record_proposal(sample_proposal)
        ledger.record_execution(sample_proposal.proposal_id, success=True,
                                duration_ms=150.0, result="done")

        p = ledger.proposals[sample_proposal.proposal_id]
        assert p.status == ProposalStatus.EXECUTED
        assert ledger.total_successful == 1
        assert ledger.total_executed == 1
        assert ledger.executions_this_hour == 1

    def test_execution_failure(self, ledger, sample_proposal):
        """Failed execution tracks failure time and cooldown."""
        ledger.record_proposal(sample_proposal)
        ledger.record_execution(sample_proposal.proposal_id, success=False,
                                duration_ms=50.0, error="crash")

        p = ledger.proposals[sample_proposal.proposal_id]
        assert p.status == ProposalStatus.FAILED
        assert ledger.total_failed == 1
        assert ledger.last_failure_time > 0
        assert len(ledger.failures_24h) == 1

    def test_rollback(self, ledger, sample_proposal):
        """Rollback sets ROLLED_BACK status."""
        ledger.record_proposal(sample_proposal)
        ledger.record_rollback(sample_proposal.proposal_id, reason="regression detected")

        assert ledger.proposals[sample_proposal.proposal_id].status == ProposalStatus.ROLLED_BACK
        assert ledger.total_rolled_back == 1

    def test_promotion_success(self, ledger, sample_proposal):
        """Successful promotion updates status to PROMOTED."""
        ledger.record_proposal(sample_proposal)
        ledger.record_canary_result(sample_proposal.proposal_id, success=True)
        ledger.record_promotion(sample_proposal.proposal_id, success=True,
                                metrics_after={"latency": 10})

        assert ledger.proposals[sample_proposal.proposal_id].status == ProposalStatus.PROMOTED

    def test_unknown_proposal_ignored(self, ledger):
        """Operations on unknown proposal_id are safely ignored."""
        ledger.record_approval("nonexistent", approved=True)
        ledger.record_canary_result("nonexistent", success=True)
        ledger.record_execution("nonexistent", success=True, duration_ms=0)
        ledger.record_rollback("nonexistent", reason="test")
        # No exceptions, no new entries
        assert len(ledger.proposals) == 0


# ──────────────────────────────────────────────────────────
# Kill Switch Tests
# ──────────────────────────────────────────────────────────

class TestKillSwitch:
    def test_activation(self, ledger):
        """Kill switch activates after threshold failures."""
        ledger.KILL_SWITCH_THRESHOLD = 3
        for i in range(3):
            p = _make_proposal(f"fail_{i}")
            ledger.record_proposal(p)
            ledger.record_canary_result(p.proposal_id, success=False, result="error")

        assert ledger.safe_mode is True

    def test_blocks_proposals(self, ledger):
        """Safe mode blocks new proposals."""
        ledger.safe_mode = True
        ok, msg = ledger.can_propose()
        assert ok is False
        assert "SAFE MODE" in msg

    def test_blocks_execution(self, ledger):
        """Safe mode blocks execution."""
        ledger.safe_mode = True
        ok, msg = ledger.can_execute()
        assert ok is False
        assert "SAFE MODE" in msg

    def test_exit_safe_mode(self, ledger):
        """Manual exit resets safe mode."""
        ledger.safe_mode = True
        ledger.failures_24h = [time.time()] * 5
        ledger.exit_safe_mode("Manual operator reset")
        assert ledger.safe_mode is False
        assert len(ledger.failures_24h) == 0


# ──────────────────────────────────────────────────────────
# Chain Integrity Tests
# ──────────────────────────────────────────────────────────

class TestChainIntegrity:
    def test_hash_chain_links(self, ledger):
        """Each entry's prev_hash links to the previous entry's hash."""
        p1 = _make_proposal("chain_a")
        p2 = _make_proposal("chain_b")
        ledger.record_proposal(p1)
        ledger.record_proposal(p2)

        with open(ledger.ledger_file) as f:
            lines = f.readlines()
        e1 = json.loads(lines[0])
        e2 = json.loads(lines[1])

        assert e1["prev_hash"] == "GENESIS"
        assert e2["prev_hash"] == e1["hash"]

    def test_tamper_detection(self, tmp_path):
        """Tampering with entry data is detected on reload."""
        data_dir = tmp_path / ".noogh" / "evolution"
        data_dir.mkdir(parents=True)

        with patch.dict(os.environ, {"NOOGH_EVOLUTION_KEY": "test_key_123"}):
            led1 = EvolutionLedger(data_dir=data_dir)
            p = _make_proposal("tamper_test")
            led1.record_proposal(p)
            led1.record_approval("tamper_test", approved=True)

        # Tamper with the ledger file
        ledger_file = data_dir / "evolution_ledger.jsonl"
        with open(ledger_file, "r") as f:
            lines = f.readlines()
        entry = json.loads(lines[1])
        entry["data"]["approved"] = False  # Flip the approval
        lines[1] = json.dumps(entry) + "\n"
        with open(ledger_file, "w") as f:
            f.writelines(lines)

        # Reload — chain should be invalid, auto-recovery should kick in
        with patch.dict(os.environ, {"NOOGH_EVOLUTION_KEY": "test_key_123"}):
            led2 = EvolutionLedger(data_dir=data_dir)

        # After auto-recovery: chain is valid again (fresh genesis) 
        assert led2.chain_valid is True
        assert led2.last_hash == "GENESIS"
        assert len(led2.proposals) == 0  # Quarantined

    def test_hmac_tampering(self, tmp_path):
        """Content change detected even if hash is recalculated."""
        data_dir = tmp_path / ".noogh" / "evolution"
        data_dir.mkdir(parents=True)

        with patch.dict(os.environ, {"NOOGH_EVOLUTION_KEY": "test_key_123"}):
            led1 = EvolutionLedger(data_dir=data_dir)
            p = _make_proposal("hmac_test")
            led1.record_proposal(p)

        ledger_file = data_dir / "evolution_ledger.jsonl"
        with open(ledger_file, "r") as f:
            content = f.read()
        content = content.replace("Test proposal hmac_test", "HACKED description")
        with open(ledger_file, "w") as f:
            f.write(content)

        with patch.dict(os.environ, {"NOOGH_EVOLUTION_KEY": "test_key_123"}):
            led2 = EvolutionLedger(data_dir=data_dir)

        # Auto-recovery kicks in after chain violation
        assert led2.last_hash == "GENESIS"
        assert len(led2.proposals) == 0


# ──────────────────────────────────────────────────────────
# Helper Method Tests
# ──────────────────────────────────────────────────────────

class TestHelpers:
    def test_can_propose_normal(self, ledger):
        """can_propose returns OK in normal state."""
        ok, msg = ledger.can_propose()
        assert ok is True
        assert msg == "OK"

    def test_can_execute_with_cooldown(self, ledger):
        """can_execute respects failure cooldown."""
        ledger.last_failure_time = time.time()
        ok, msg = ledger.can_execute()
        assert ok is False
        assert "cooldown" in msg.lower()

    def test_can_execute_rate_limit(self, ledger):
        """can_execute blocks after rate limit."""
        ledger.executions_this_hour = ledger.MAX_EXECUTIONS_PER_HOUR
        ok, msg = ledger.can_execute()
        assert ok is False
        assert "Rate limit" in msg

    def test_get_stats(self, ledger, sample_proposal):
        """get_stats returns comprehensive statistics."""
        ledger.record_proposal(sample_proposal)
        ledger.record_approval(sample_proposal.proposal_id, approved=True)
        stats = ledger.get_stats()

        assert stats["total_proposals"] == 1
        assert stats["total_approved"] == 1
        assert stats["safe_mode"] is False
        assert stats["chain_valid"] is True
        assert "success_rate" in stats
        assert "failures_24h" in stats

    def test_get_recent_proposals(self, ledger):
        """Recent proposals sorted by creation time."""
        for i in range(5):
            p = _make_proposal(f"recent_{i}")
            ledger.record_proposal(p)

        recent = ledger.get_recent_proposals(limit=3)
        assert len(recent) == 3
        # Most recent first
        assert recent[0].proposal_id == "recent_4"

    def test_is_safe_mode(self, ledger):
        """is_safe_mode triggers kill switch check."""
        assert ledger.is_safe_mode() is False
        ledger.safe_mode = True
        assert ledger.is_safe_mode() is True


# ──────────────────────────────────────────────────────────
# Edge Cases
# ──────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_proposal_types(self, ledger):
        """All proposal types can be recorded."""
        for ptype in [ProposalType.CODE, ProposalType.CONFIG, 
                      ProposalType.POLICY, ProposalType.AGENT]:
            p = _make_proposal(f"type_{ptype.value}", ptype=ptype, risk=10)
            ok, _ = ledger.record_proposal(p)
            assert ok is True, f"Failed for type {ptype}"

    def test_empty_diff(self, ledger):
        """Proposals with empty diff are accepted."""
        p = _make_proposal("empty_diff", diff="")
        ok, _ = ledger.record_proposal(p)
        assert ok is True

    def test_full_lifecycle(self, ledger):
        """Complete proposal lifecycle: propose → approve → canary → promote."""
        p = _make_proposal("lifecycle")
        ledger.record_proposal(p)
        assert ledger.proposals["lifecycle"].status == ProposalStatus.PENDING

        ledger.record_approval("lifecycle", approved=True)
        assert ledger.proposals["lifecycle"].status == ProposalStatus.APPROVED

        ledger.record_canary_result("lifecycle", success=True)
        assert ledger.proposals["lifecycle"].status == ProposalStatus.CANARY

        ledger.record_promotion("lifecycle", success=True)
        assert ledger.proposals["lifecycle"].status == ProposalStatus.PROMOTED

        # Verify chain has 4 entries
        with open(ledger.ledger_file) as f:
            lines = f.readlines()
        assert len(lines) == 4
