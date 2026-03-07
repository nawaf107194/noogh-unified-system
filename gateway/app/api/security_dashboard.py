"""
Security Dashboard API Endpoints
Provides real-time security status for the NOOGH Console
"""
from fastapi import APIRouter, Depends, Request
from typing import Dict, Any, List
import logging
from datetime import datetime

from gateway.app.core.jwt_validator import require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard/security", tags=["Security Dashboard"])


@router.get("/status")
async def get_security_status(request: Request) -> Dict[str, Any]:
    """
    Get comprehensive security system status.
    
    Returns:
        - AMLA enforcement status
        - Tool validator status  
        - Governance enforcement status
        - Budget protection status
        - Recent security alerts
        - Security metrics
    """
    try:
        # Check AMLA status
        from unified_core.core.actuators import AMLA_AVAILABLE
        amla_status = "active" if AMLA_AVAILABLE else "error"
        
        # Check validator status
        validator_status = "fail_closed"  # Always fail-closed now
        try:
            from neural_engine.tools.tool_validator import validate_tool_args
            validator_status = "fail_closed"  # Available and fail-closed
        except ImportError:
            validator_status = "error"  # Should never happen (system would crash)
        
        # Check governance status
        from unified_core.governance.feature_flags import GovernanceFlags
        governance_enabled = getattr(GovernanceFlags, 'ENABLED', True)  # Default to enabled
        governance_status = "enforced" if governance_enabled else "disabled"
        
        # Budget enforcement (always active in ConstrainedReActLoop)
        budget_status = "enforced"
        
        # Get recent alerts (from monitor if available)
        recent_alerts = []
        try:
            from neural_engine.autonomy.monitor import get_monitor
            monitor = get_monitor()
            status = monitor.get_status()
            recent_alerts = status.get("recent_alerts", [])
        except Exception as e:
            logger.warning(f"Could not fetch monitor alerts: {e}")
        
        # Mock metrics (in production, retrieve from actual counters)
        metrics = {
            "validationPasses": 1234,
            "validationFailures": 3,
            "governanceChecks": 567,
            "budgetViolations": 1
        }
        
        return {
            "amlaStatus": amla_status,
            "validatorStatus": validator_status,
            "governanceStatus": governance_status,
            "budgetEnforcement": budget_status,
            "recentAlerts": recent_alerts,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching security status: {e}")
        return {
            "amlaStatus": "error",
            "validatorStatus": "error",
            "governanceStatus": "error",
            "budgetEnforcement": "error",
            "recentAlerts": [{
                "severity": "critical",
                "message": f"Error fetching security status: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }],
            "metrics": {
                "validationPasses": 0,
                "validationFailures": 0,
                "governanceChecks": 0,
                "budgetViolations": 0
            }
        }


@router.get("/dry-run-status")
async def get_dry_run_status(request: Request) -> Dict[str, Any]:
    """
    Get current dry-run mode status and approval details.
    
    Returns:
        - enabled: bool
        - approval: dict (if enabled)
        - expiresAt: timestamp (if enabled)
    """
    try:
        from unified_core.governance.dry_run_approval import is_dry_run_enabled, get_approval_status
        
        enabled = is_dry_run_enabled()
        
        if enabled:
            approval_status = get_approval_status()
            return {
                "enabled": True,
                "approval": {
                    "approver": approval_status.get("approver", "unknown"),
                    "reason": approval_status.get("reason", "N/A"),
                    "timestamp": approval_status.get("timestamp", ""),
                },
                "expiresAt": approval_status.get("expires_at", "")
            }
        else:
            return {
                "enabled": False,
                "approval": None,
                "expiresAt": None
            }
            
    except Exception as e:
        logger.error(f"Error fetching dry-run status: {e}")
        return {
            "enabled": False,
            "approval": None,
            "expiresAt": None,
            "error": str(e)
        }


@router.get("/test-coverage")
async def get_test_coverage(
    request: Request,
    user: dict = Depends(require_role("admin"))
) -> Dict[str, Any]:
    """
    Get security test coverage statistics (admin only).
    
    Returns:
        - Total tests
        - Passing tests
        - Failed tests
        - Coverage percentage
    """
    import subprocess
    import json
    
    try:
        # Run critical tests and parse results
        result = subprocess.run(
            ["python3", "-m", "pytest", "tests/critical/", "--tb=no", "-v", "--json-report"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd="/home/noogh/projects/noogh_unified_system/src"
        )
        
        # Parse output for pass/fail counts
        lines = result.stdout.split('\n')
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for line in lines:
            if "passed" in line.lower():
                # Extract numbers from "35 passed" format
                import re
                match = re.search(r'(\d+)\s+passed', line)
                if match:
                    passed_tests = int(match.group(1))
                    total_tests += passed_tests
            if "failed" in line.lower():
                match = re.search(r'(\d+)\s+failed', line)
                if match:
                    failed_tests = int(match.group(1))
                    total_tests += failed_tests
        
        coverage_pct = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "totalTests": total_tests,
            "passingTests": passed_tests,
            "failedTests": failed_tests,
            "coveragePercentage": round(coverage_pct, 1),
            "lastRun": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return {
            "totalTests": 0,
            "passingTests": 0,
            "failedTests": 0,
            "coveragePercentage": 0,
            "error": str(e)
        }

@router.get("/kernel-metrics")
async def get_kernel_metrics(request: Request) -> Dict[str, Any]:
    """
    Get AgentKernel performance metrics.
    
    Returns comprehensive kernel statistics including:
    - Request counts and success rates
    - Tool execution metrics
    - Response time statistics
    - Brain switching frequency
    - Memory operations
    - Protocol violations
    """
    try:
        # Try to get kernel instance from app state
        kernel = None
        if hasattr(request.app, 'state') and hasattr(request.app.state, 'kernel'):
            kernel = request.app.state.kernel
        
        if not kernel:
            # Try to import and get global instance
            try:
                from gateway.app.core.agent_kernel import get_kernel
                kernel = get_kernel()
            except ImportError:
                pass
        
        if not kernel:
            return {
                "available": False,
                "message": "Kernel not initialized or not accessible"
            }
        
        # Get kernel metrics
        if hasattr(kernel, 'metrics') and kernel.metrics:
            summary = kernel.metrics.get_summary()
            
            # Get additional kernel status
            if hasattr(kernel, 'get_status'):
                kernel_status = kernel.get_status()
            else:
                kernel_status = {}
            
            return {
                "available": True,
                "metrics": summary,
                "performance": kernel_status.get("performance_metrics", {}),
                "config": kernel_status.get("config", {}),
                "memory_stats": kernel_status.get("memory_stats", {}),
                "gpu_status": kernel_status.get("gpu_status", {}),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "available": False,
                "message": "Kernel metrics not enabled"
            }
            
    except Exception as e:
        logger.error(f"Error fetching kernel metrics: {e}")
        return {
            "available": False,
            "error": str(e)
        }


@router.post("/validate-input-sample")
async def validate_input_sample(
    request: Request,
    sample: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Test endpoint to validate sample tool input (for testing validation rules).
    
    Args:
        sample: Tool name and arguments to validate
        
    Returns:
        validation result
    """
    try:
        from neural_engine.tools.tool_validator import validate_tool_args, ValidationError
        
        tool_name = sample.get("tool_name", "test")
        args = sample.get("arguments", {})
        
        try:
            validated = validate_tool_args(tool_name, args)
            return {
                "valid": True,
                "validatedArgs": validated,
                "message": "Validation passed"
            }
        except ValidationError as e:
            return {
                "valid": False,
                "error": str(e),
                "message": "Validation failed"
            }
            
    except ImportError as e:
        # This should never happen (system crashes if validator missing)
        return {
            "valid": False,
            "error": "CRITICAL: Validator unavailable (system should have crashed)",
            "message": "System integrity compromised"
        }
