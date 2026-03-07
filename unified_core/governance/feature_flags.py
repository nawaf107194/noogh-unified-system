"""
Governance Feature Flags

Controls which governance features are enabled.

SECURITY UPDATE (Day 7): Changed to OPT-OUT model.
- Governance is NOW ENABLED BY DEFAULT for security
- Must explicitly disable via NOOGH_GOVERNANCE_DISABLED=1
- Production systems should NEVER disable governance
"""

import logging
import os
from typing import Dict, Optional

logger = logging.getLogger("unified_core.governance.feature_flags")


class GovernanceFlags:
    """
    Feature flags for governance layer.
    
    SECURITY MODEL (Day 7 Update):
    - OPT-OUT: Governance enabled by default
    - Must explicitly set NOOGH_GOVERNANCE_DISABLED=1 to disable
    - All flags default to governance-enabled state
    """
    
    # =========================================================================
    # MASTER GOVERNANCE SWITCH (OPT-OUT MODEL)
    # =========================================================================
    
    # Changed from opt-IN to opt-OUT for security
    # OLD (DAY 0-6): GOVERNANCE_ENABLED = os.getenv("NOOGH_GOVERNANCE_ENABLED", "0") == "1"
    # NEW (DAY 7+): Enabled by default, must opt-OUT
    GOVERNANCE_ENABLED: bool = os.getenv("NOOGH_GOVERNANCE_DISABLED", "0") != "1"
    
    # =========================================================================
    # COMPONENT-LEVEL GOVERNANCE FLAGS
    # =========================================================================
    
    # Individual gates
    AUTH_GATE_ENABLED: bool = os.getenv("NOOGH_AUTH_GATE_DISABLED", "0") != "1"
    APPROVAL_GATE_ENABLED: bool = os.getenv("NOOGH_APPROVAL_GATE_DISABLED", "0") != "1"
    CIRCUIT_BREAKER_ENABLED: bool = os.getenv("NOOGH_CIRCUIT_BREAKER_DISABLED", "0") != "1"
    AUDIT_LOG_ENABLED: bool = os.getenv("NOOGH_AUDIT_LOG_DISABLED", "0") != "1"
    
    # Per-component wrapping
    WRAP_PROCESS_SPAWN: bool = os.getenv("NOOGH_WRAP_PROCESS_SPAWN_DISABLED", "0") != "1"
    WRAP_PROCESS_KILL: bool = os.getenv("NOOGH_WRAP_PROCESS_KILL_DISABLED", "0") != "1"
    WRAP_FS_DELETE: bool = os.getenv("NOOGH_WRAP_FS_DELETE_DISABLED", "0") != "1"
    WRAP_NETWORK_HTTP: bool = os.getenv("NOOGH_WRAP_NETWORK_HTTP_DISABLED", "0") != "1"
    
    # Dry-run mode (requires cryptographic approval)
    # SECURITY: Cannot be enabled via ENV var alone
    _DRY_RUN_CACHED: Optional[bool] = None
    _DRY_RUN_LAST_CHECK: float = 0.0
    _DRY_RUN_CHECK_INTERVAL: float = 60.0  # Re-check every 60 seconds
    
    @classmethod
    def DRY_RUN(cls) -> bool:
        """
        Check if dry-run mode is enabled.
        
        SECURITY: Requires signed approval file, not just ENV var.
        Cached for 60 seconds to avoid excessive filesystem checks.
        """
        import time
        
        current_time = time.time()
        
        # Check cache
        if (cls._DRY_RUN_CACHED is not None and 
            current_time - cls._DRY_RUN_LAST_CHECK < cls._DRY_RUN_CHECK_INTERVAL):
            return cls._DRY_RUN_CACHED
        
        # Re-check approval
        try:
            from unified_core.governance.dry_run_approval import is_dry_run_enabled
            enabled = is_dry_run_enabled()
        except ImportError:
            # Approval system not available - default to disabled
            logger.warning("Dry-run approval system unavailable - defaulting to disabled")
            enabled = False
        except Exception as e:
            # Unexpected error - fail closed
            logger.error(f"Error checking dry-run approval: {e}")
            enabled = False
        
        # Update cache
        cls._DRY_RUN_CACHED = enabled
        cls._DRY_RUN_LAST_CHECK = current_time
        
        return enabled
    
    @classmethod
    def is_enabled_for(cls, component: str) -> bool:
        """
        Check if governance is enabled for a specific component.
        
        Args:
            component: Component name (e.g., "filesystem.delete", "process.spawn")
        
        Returns:
            True if governance is enabled for this component
        """
        if not cls.GOVERNANCE_ENABLED:
            return False
        
        component_flags = {
            "process.spawn": cls.WRAP_PROCESS_SPAWN,
            "process.kill": cls.WRAP_PROCESS_KILL,
            "filesystem.delete": cls.WRAP_FS_DELETE,
            "network.http": cls.WRAP_NETWORK_HTTP,
        }
        
        return component_flags.get(component, False)
    
    @classmethod
    def get_status(cls) -> Dict[str, bool]:
        """Get current flag status (for debugging)"""
        status = {
            "governance_enabled": cls.GOVERNANCE_ENABLED,
            "auth_gate": cls.AUTH_GATE_ENABLED,
            "approval_gate": cls.APPROVAL_GATE_ENABLED,
            "circuit_breaker": cls.CIRCUIT_BREAKER_ENABLED,
            "audit_log": cls.AUDIT_LOG_ENABLED,
            "dry_run": cls.DRY_RUN,
            "components": {
                "process.spawn": cls.WRAP_PROCESS_SPAWN,
                "process.kill": cls.WRAP_PROCESS_KILL,
                "filesystem.delete": cls.WRAP_FS_DELETE,
                "network.http": cls.WRAP_NETWORK_HTTP,
            }
        }
        
        if cls.GOVERNANCE_ENABLED:
            logger.info("✅ GOVERNANCE ENABLED (opt-out model)")
        else:
            logger.warning("⚠️ GOVERNANCE DISABLED - This should ONLY be used for development/debugging!")
        
        return status


# Export singleton
flags = GovernanceFlags()
