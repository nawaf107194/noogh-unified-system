# This file contains documentation examples only.
# It is not imported at runtime.

if False:
    """
    # NOTE: This is documentation/example code, not runnable production code.
    from unified_core.auth import AuthContext
    auth_context = AuthContext(user_id="example", role="admin", scopes=["*"])
    auth = auth_context
    Example: Wrapping ProcessActuator with Governed Spine
    
    Demonstrates how to wrap critical operations WITHOUT modifying subsystems.
    """
    
    # BEFORE (original code - unchanged)
    # =====================================
    """
    from unified_core.core.actuators import ProcessActuator
    
    actuator = ProcessActuator()
    result = actuator.spawn(["sleep", "10"], auth_context=auth)
    """
    
    # AFTER (with governance wrapper)
    # =====================================
    from unified_core.core.actuators import ProcessActuator
    from unified_core.governance import execution_envelope
    from unified_core.decision_classifier import DecisionImpact
    
    actuator = ProcessActuator()
    
    # Wrap the call with governance
    with execution_envelope(
        auth=auth_context,
        component="process.spawn",
        impact=DecisionImpact.CRITICAL,
        params={"cmd": ["sleep", "10"]}
    ):
        # Original call UNCHANGED
        result = actuator.spawn(["sleep", "10"], auth_context=auth)
    
    # That's it! No subsystem modifications needed.
    
    
    # =====================================
    # FULL EXAMPLE with all 3 components
    # =====================================
    
    def governed_process_operations():
        """Example of governed process operations."""
        from unified_core.core.actuators import ProcessActuator
        from unified_core.governance import execution_envelope
        from unified_core.decision_classifier import DecisionImpact
        
        actuator = ProcessActuator()
        auth = ...  # Your auth_context
        
        # 1. Governed spawn
        with execution_envelope(
            auth=auth,
            component="process.spawn",
            impact=DecisionImpact.CRITICAL
        ):
            result = actuator.spawn(["ls", "-la"], auth_context=auth)
            pid = result.result_data["pid"]
            nonce = result.result_data.get("nonce")  # If Phase 4 integrated
        
        # 2. Governed kill
        with execution_envelope(
            auth=auth,
            component="process.kill",
            impact=DecisionImpact.CRITICAL,
            params={"pid": pid}
        ):
            actuator.kill(pid, nonce, auth_context=auth)  # Phase 4 signature
        
        return result
    
    
    # =====================================
    # Testing in Dry-Run Mode
    # =====================================
    
    def test_dry_run():
        """Test governance without enforcement."""
        from unified_core.governance import flags, execution_envelope
        
        # Enable dry-run
        flags.GOVERNANCE_ENABLED = True
        flags.DRY_RUN = True
        
        # This will LOG but not BLOCK (even with missing auth)
        with execution_envelope(
            auth=None,  # Missing auth!
            component="process.spawn"
        ):
            print("Executed in dry-run mode")
        
        # Check logs:
        # [GOVERNANCE] execution_started | component=process.spawn | user=unknown
        # [DRY-RUN] Missing auth for process.spawn
        # [GOVERNANCE] execution_completed | component=process.spawn
    
    
    # =====================================
    # Gradual Rollout Pattern
    # =====================================
    
    def gradual_rollout_example():
        """Demonstrate gradual activation."""
        from unified_core.governance import flags, execution_envelope
        
        # Week 1: Dry-run only
        flags.GOVERNANCE_ENABLED = True
        flags.DRY_RUN = True
        flags.WRAP_PROCESS_SPAWN = True
        
        # Week 2: Enable auth gate (still dry-run for approval)
        flags.AUTH_GATE_ENABLED = True
        flags.DRY_RUN = True  # Still logging approval checks
        
        # Week 3: Full enforcement
        flags.APPROVAL_GATE_ENABLED = True
        flags.DRY_RUN = False  # Now enforcing!
    
    
    # =====================================
    # Event Monitoring
    # =====================================
    
    def setup_monitoring():
        """Subscribe to governance events."""
        from unified_core.governance import (
            get_observability_bus,
            GovernanceEventType
        )
        
        bus = get_observability_bus()
        
        def security_monitor(event):
            """Monitor security-critical events."""
            if event.event_type == GovernanceEventType.EXECUTION_BLOCKED:
                print(f"🚨 BLOCKED: {event.component} by {event.user_id}")
            
            elif event.event_type == GovernanceEventType.EXECUTION_FAILED:
                print(f"❌ FAILED: {event.component} - {event.metadata.get('error')}")
        
        # Subscribe to all events
        bus.subscribe(None, security_monitor)
    
    
    # =====================================
    # Rollback Example
    # =====================================
    
    def rollback_if_needed():
        """How to rollback governance if issues occur."""
        from unified_core.governance import flags
        
        # Emergency: Disable all governance
        flags.GOVERNANCE_ENABLED = False
        
        # Or: Disable specific component
        flags.WRAP_PROCESS_SPAWN = False
        
        # Or: Revert to dry-run
        flags.DRY_RUN = True
        
        print(f"Governance status: {flags.get_status()}")
    
    
    if __name__ == "__main__":
        # Test dry-run mode
        test_dry_run()
        
        # Setup monitoring
        setup_monitoring()
        
        print("✅ Governed Spine examples loaded successfully")
    
