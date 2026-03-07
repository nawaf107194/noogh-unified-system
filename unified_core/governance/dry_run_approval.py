"""
Dry-Run Approval System
Requires cryptographic approval to enable dry-run governance mode.

SECURITY MODEL:
- Dry-run mode MUST be approved via signed file
- File location: /var/noogh/dry_run_approved.sig
- Contains: timestamp, approver, signature
- Audited on every check
"""
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Configuration
DRY_RUN_APPROVAL_FILE = Path("/var/noogh/dry_run_approved.sig")
DRY_RUN_AUDIT_LOG = Path("/var/log/noogh/dry_run_activations.log")
MAX_APPROVAL_AGE_HOURS = 24  # Approval expires after 24 hours


class DryRunApprovalError(Exception):
    """Raised when dry-run approval is invalid or missing."""
    pass


def _log_audit(event: str, details: dict):
    """
    Log to immutable audit trail.
    """
    try:
        DRY_RUN_AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "event": event,
            **details
        }
        
        # Append-only logging
        with DRY_RUN_AUDIT_LOG.open("a") as f:
            f.write(json.dumps(log_entry) + "\n")
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
            
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
        # Don't fail operation on audit failure, but log critically
        logger.critical(f"AUDIT FAILURE: Dry-run event not logged: {event}")


def check_dry_run_approval() -> Tuple[bool, Optional[str]]:
    """
    Check if dry-run mode is approved.
    
    Returns:
        (approved: bool, reason: Optional[str])
        
    Raises:
        DryRunApprovalError: On security violations
    """
    # Check environment variable first (legacy support)
    env_dry_run = os.getenv("NOOGH_GOVERNANCE_DRY_RUN", "0")
    
    if env_dry_run != "1":
        # Dry-run not requested via ENV
        return False, None
    
    # Dry-run requested - verify approval file
    _log_audit("dry_run_check", {
        "env_var": env_dry_run,
        "approval_file": str(DRY_RUN_APPROVAL_FILE),
        "source": "environment_variable"
    })
    
    if not DRY_RUN_APPROVAL_FILE.exists():
        error = (
            f"SECURITY VIOLATION: Dry-run requested via ENV but approval file missing. "
            f"Expected: {DRY_RUN_APPROVAL_FILE}"
        )
        logger.critical(error)
        _log_audit("dry_run_denied", {
            "reason": "missing_approval_file",
            "critical": True
        })
        raise DryRunApprovalError(error)
    
    # Read approval file
    try:
        approval_data = json.loads(DRY_RUN_APPROVAL_FILE.read_text())
    except Exception as e:
        error = f"SECURITY VIOLATION: Invalid approval file format: {e}"
        logger.critical(error)
        _log_audit("dry_run_denied", {
            "reason": "invalid_file_format",
            "error": str(e),
            "critical": True
        })
        raise DryRunApprovalError(error)
    
    # Validate required fields
    required_fields = ["timestamp", "approver", "reason", "signature"]
    missing = [f for f in required_fields if f not in approval_data]
    if missing:
        error = f"SECURITY VIOLATION: Approval file missing fields: {missing}"
        logger.critical(error)
        _log_audit("dry_run_denied", {
            "reason": "missing_fields",
            "missing_fields": missing,
            "critical": True
        })
        raise DryRunApprovalError(error)
    
    # Check timestamp (approval must not be expired)
    try:
        approved_at = datetime.fromisoformat(approval_data["timestamp"])
        age = datetime.utcnow() - approved_at
        
        if age > timedelta(hours=MAX_APPROVAL_AGE_HOURS):
            error = (
                f"SECURITY VIOLATION: Dry-run approval expired. "
                f"Age: {age}, Max: {MAX_APPROVAL_AGE_HOURS}h"
            )
            logger.critical(error)
            _log_audit("dry_run_denied", {
                "reason": "expired_approval",
                "age_hours": age.total_seconds() / 3600,
                "max_hours": MAX_APPROVAL_AGE_HOURS,
                "critical": True
            })
            raise DryRunApprovalError(error)
            
    except ValueError as e:
        error = f"SECURITY VIOLATION: Invalid timestamp format: {e}"
        logger.critical(error)
        _log_audit("dry_run_denied", {
            "reason": "invalid_timestamp",
            "error": str(e),
            "critical": True
        })
        raise DryRunApprovalError(error)
    
    # Verify signature
    expected_signature = _compute_signature(approval_data)
    if approval_data["signature"] != expected_signature:
        error = "SECURITY VIOLATION: Invalid signature on dry-run approval"
        logger.critical(error)
        _log_audit("dry_run_denied", {
            "reason": "invalid_signature",
            "critical": True
        })
        raise DryRunApprovalError(error)
    
    # All checks passed
    logger.warning(
        f"⚠️ DRY-RUN MODE APPROVED: {approval_data['reason']} "
        f"(Approver: {approval_data['approver']}, Age: {age})"
    )
    
    _log_audit("dry_run_approved", {
        "approver": approval_data["approver"],
        "reason": approval_data["reason"],
        "age_hours": age.total_seconds() / 3600,
        "warning": "governance_bypassed"
    })
    
    return True, approval_data["reason"]


def _compute_signature(data: dict) -> str:
    """
    Compute signature for approval data.
    
    Simple HMAC using system secret. In production, use GPG or similar.
    """
    # Get system secret (should be in vault in production)
    secret = os.getenv("NOOGH_SECRET_KEY", "default-dev-secret")
    
    # Create canonical representation
    canonical = f"{data['timestamp']}:{data['approver']}:{data['reason']}:{secret}"
    
    # Compute hash
    return hashlib.sha256(canonical.encode()).hexdigest()


def create_dry_run_approval(approver: str, reason: str) -> Path:
    """
    Create a dry-run approval file.
    
    SECURITY: This should only be callable by authorized administrators.
    
    Args:
        approver: Name/ID of person approving
        reason: Justification for dry-run mode
        
    Returns:
        Path to created approval file
    """
    timestamp = datetime.utcnow().isoformat()
    
    approval_data = {
        "timestamp": timestamp,
        "approver": approver,
        "reason": reason,
        "signature": ""  # Will be computed
    }
    
    # Compute signature
    approval_data["signature"] = _compute_signature(approval_data)
    
    # Ensure directory exists
    DRY_RUN_APPROVAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Write approval file
    DRY_RUN_APPROVAL_FILE.write_text(json.dumps(approval_data, indent=2))
    
    logger.warning(
        f"⚠️ DRY-RUN APPROVAL CREATED: {reason} (Approver: {approver})"
    )
    
    _log_audit("approval_created", {
        "approver": approver,
        "reason": reason,
        "expires_at": (datetime.utcnow() + timedelta(hours=MAX_APPROVAL_AGE_HOURS)).isoformat()
    })
    
    return DRY_RUN_APPROVAL_FILE


def revoke_dry_run_approval():
    """Revoke dry-run approval by deleting the file."""
    if DRY_RUN_APPROVAL_FILE.exists():
        DRY_RUN_APPROVAL_FILE.unlink()
        logger.info("Dry-run approval revoked")
        _log_audit("approval_revoked", {})
    else:
        logger.info("No dry-run approval to revoke")


def is_dry_run_enabled() -> bool:
    """
    Check if dry-run mode is currently enabled and approved.
    
    Returns:
        True if dry-run is enabled and approved, False otherwise
    """
    try:
        approved, _ = check_dry_run_approval()
        return approved
    except DryRunApprovalError:
        # Approval check failed - dry-run NOT enabled
        return False
    except Exception as e:
        # Unexpected error - fail closed
        logger.error(f"Unexpected error checking dry-run approval: {e}")
        return False


def get_approval_status() -> dict:
    """
    Get detailed dry-run approval status for dashboard display.
    
    Returns:
        dict with approval details or empty dict if not approved
    """
    if not DRY_RUN_APPROVAL_FILE.exists():
        return {}
    
    try:
        approval_data = json.loads(DRY_RUN_APPROVAL_FILE.read_text())
        
        # Calculate expiration
        approved_at = datetime.fromisoformat(approval_data["timestamp"])
        expires_at = approved_at + timedelta(hours=MAX_APPROVAL_AGE_HOURS)
        
        return {
            "approver": approval_data.get("approver", "unknown"),
            "reason": approval_data.get("reason", "N/A"),
            "timestamp": approval_data.get("timestamp", ""),
            "expires_at": expires_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error reading approval status: {e}")
        return {}


# Export
__all__ = [
    "check_dry_run_approval",
    "create_dry_run_approval",
    "revoke_dry_run_approval",
    "is_dry_run_enabled",
    "get_approval_status",  # NEW
    "DryRunApprovalError",
]
