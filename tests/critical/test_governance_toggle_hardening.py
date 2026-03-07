"""
Test Dry-Run Approval System
Tests the governance bypass approval mechanism.
"""
import json
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

# We'll mock the file paths during tests
from unified_core.governance import dry_run_approval


class TestDryRunApproval:
    """Test dry-run approval system."""
    
    def test_no_env_var_no_approval(self, monkeypatch):
        """If ENV var is not set, dry-run should be disabled."""
        monkeypatch.setenv("NOOGH_GOVERNANCE_DRY_RUN", "0")
        
        approved, reason =dry_run_approval.check_dry_run_approval()
        assert approved is False
        assert reason is None
    
    def test_env_var_without_file_raises(self, monkeypatch, tmp_path):
        """If ENV is set but approval file missing, should raise."""
        monkeypatch.setenv("NOOGH_GOVERNANCE_DRY_RUN", "1")
        
        # Mock file path to non-existent location
        fake_path = tmp_path / "nonexistent" / "approval.sig"
        monkeypatch.setattr(
            dry_run_approval,
            "DRY_RUN_APPROVAL_FILE",
            fake_path
        )
        
        with pytest.raises(dry_run_approval.DryRunApprovalError) as exc:
            dry_run_approval.check_dry_run_approval()
        
        assert "missing" in str(exc.value).lower()
    
    def test_invalid_json_raises(self, monkeypatch, tmp_path):
        """Invalid JSON in approval file should raise."""
        monkeypatch.setenv("NOOGH_GOVERNANCE_DRY_RUN", "1")
        
        # Create invalid JSON file
        approval_file = tmp_path / "approval.sig"
        approval_file.write_text("not valid json{")
        
        monkeypatch.setattr(
            dry_run_approval,
            "DRY_RUN_APPROVAL_FILE",
            approval_file
        )
        
        with pytest.raises(dry_run_approval.DryRunApprovalError) as exc:
            dry_run_approval.check_dry_run_approval()
        
        assert "invalid" in str(exc.value).lower()
    
    def test_missing_fields_raises(self, monkeypatch, tmp_path):
        """Approval file missing required fields should raise."""
        monkeypatch.setenv("NOOGH_GOVERNANCE_DRY_RUN", "1")
        
        # Create file with missing fields
        approval_file = tmp_path / "approval.sig"
        approval_file.write_text(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            # Missing: approver, reason, signature
        }))
        
        monkeypatch.setattr(
            dry_run_approval,
            "DRY_RUN_APPROVAL_FILE",
            approval_file
        )
        
        with pytest.raises(dry_run_approval.DryRunApprovalError) as exc:
            dry_run_approval.check_dry_run_approval()
        
        assert "missing fields" in str(exc.value).lower()
    
    def test_expired_approval_raises(self, monkeypatch, tmp_path):
        """Expired approval should raise."""
        monkeypatch.setenv("NOOGH_GOVERNANCE_DRY_RUN", "1")
        
        # Create expired approval (25 hours ago)
        old_timestamp = (datetime.utcnow() - timedelta(hours=25)).isoformat()
        approval_data = {
            "timestamp": old_timestamp,
            "approver": "test@example.com",
            "reason": "Testing",
            "signature": "invalid"  # Will be wrong anyway
        }
        
        approval_file = tmp_path / "approval.sig"
        approval_file.write_text(json.dumps(approval_data))
        
        monkeypatch.setattr(
            dry_run_approval,
            "DRY_RUN_APPROVAL_FILE",
            approval_file
        )
        
        with pytest.raises(dry_run_approval.DryRunApprovalError) as exc:
            dry_run_approval.check_dry_run_approval()
        
        assert "expired" in str(exc.value).lower()
    
    def test_invalid_signature_raises(self, monkeypatch, tmp_path):
        """Invalid signature should raise."""
        monkeypatch.setenv("NOOGH_GOVERNANCE_DRY_RUN", "1")
        
        # Create approval with wrong signature
        approval_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "approver": "test@example.com",
            "reason": "Testing",
            "signature": "wrong_signature_12345"
        }
        
        approval_file = tmp_path / "approval.sig"
        approval_file.write_text(json.dumps(approval_data))
        
        monkeypatch.setattr(
            dry_run_approval,
            "DRY_RUN_APPROVAL_FILE",
            approval_file
        )
        
        with pytest.raises(dry_run_approval.DryRunApprovalError) as exc:
            dry_run_approval.check_dry_run_approval()
        
        assert "signature" in str(exc.value).lower()
    
    def test_valid_approval_succeeds(self, monkeypatch, tmp_path):
        """Valid approval should succeed."""
        monkeypatch.setenv("NOOGH_GOVERNANCE_DRY_RUN", "1")
        monkeypatch.setenv("NOOGH_SECRET_KEY", "test-secret-123")
        
        # Mock both files to use tmp_path
        approval_file = tmp_path / "approval.sig"
        audit_log = tmp_path / "audit.log"
        
        monkeypatch.setattr(
            dry_run_approval,
            "DRY_RUN_APPROVAL_FILE",
            approval_file
        )
        monkeypatch.setattr(
            dry_run_approval,
            "DRY_RUN_AUDIT_LOG",
            audit_log
        )
        
        # Create valid approval using the create function
        dry_run_approval.create_dry_run_approval(
            "admin@example.com",
            "Testing dry-run system"
        )
        
        # Check should succeed
        approved, reason = dry_run_approval.check_dry_run_approval()
        
        assert approved is True
        assert reason == "Testing dry-run system"
    
    def test_create_and_revoke(self, monkeypatch, tmp_path):
        """Test creating and revoking approval."""
        approval_file = tmp_path / "approval.sig"
        audit_log = tmp_path / "audit.log"
        
        monkeypatch.setattr(
            dry_run_approval,
            "DRY_RUN_APPROVAL_FILE",
            approval_file
        )
        monkeypatch.setattr(
            dry_run_approval,
            "DRY_RUN_AUDIT_LOG",
            audit_log
        )
        
        # Create
        created_path = dry_run_approval.create_dry_run_approval(
            "admin",
            "Test reason"
        )
        
        assert created_path.exists()
        
        # Revoke
        dry_run_approval.revoke_dry_run_approval()
        
        assert not approval_file.exists()
    
    def test_is_dry_run_enabled_with_approval(self, monkeypatch, tmp_path):
        """Test is_dry_run_enabled() with valid approval."""
        monkeypatch.setenv("NOOGH_GOVERNANCE_DRY_RUN", "1")
        monkeypatch.setenv("NOOGH_SECRET_KEY", "test-secret")
        
        approval_file = tmp_path / "approval.sig"
        audit_log = tmp_path / "audit.log"
        
        monkeypatch.setattr(
            dry_run_approval,
            "DRY_RUN_APPROVAL_FILE",
            approval_file
        )
        monkeypatch.setattr(
            dry_run_approval,
            "DRY_RUN_AUDIT_LOG",
            audit_log
        )
        
        # Create approval
        dry_run_approval.create_dry_run_approval("admin", "Testing")
        
        # Should be enabled
        assert dry_run_approval.is_dry_run_enabled() is True
    
    def test_is_dry_run_enabled_without_approval(self, monkeypatch, tmp_path):
        """Test is_dry_run_enabled() without approval."""
        monkeypatch.setenv("NOOGH_GOVERNANCE_DRY_RUN", "1")
        
        # Point to non existent file
        fake_path = tmp_path / "nonexistent.sig"
        monkeypatch.setattr(
            dry_run_approval,
            "DRY_RUN_APPROVAL_FILE",
            fake_path
        )
        
        # Should be disabled (exception caught)
        assert dry_run_approval.is_dry_run_enabled() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
