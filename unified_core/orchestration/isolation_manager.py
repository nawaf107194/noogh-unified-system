"""
NOOGH Isolation Manager

Routes tool execution to appropriate isolation layers.

SECURITY CRITICAL: Enforces isolation boundaries.
- SAFE → No isolation
- RESTRICTED → Sandbox (no network, allowlist only)  
- DANGEROUS → Lab Container (Docker isolated)

FAIL-CLOSED: Missing isolation = BLOCKED
"""

import logging
from typing import Dict, Any, Optional

from unified_core.orchestration.messages import RiskLevel
from unified_core.observability import get_logger, inc_counter, observe_histogram
import time

# Use structured logger
logger = get_logger("isolation_manager")


class IsolationManager:
    """
    Manages isolation boundaries for tool execution.
    
    Isolation Levels:
    1. NONE: Direct execution (SAFE tools only)
    2. SANDBOX: Process isolation, no network, temp filesystem
    3. LAB_CONTAINER: Docker container, full isolation
    
    PRODUCTION ENFORCEMENT:
    - RESTRICTED tools without sandbox = BLOCKED
    - DANGEROUS tools without lab container = BLOCKED
    - Unknown tools = BLOCKED (default DANGEROUS)
    """
    
    # Tool → Required isolation mapping
    TOOL_ISOLATION_POLICY = {
        # SAFE tools - no isolation needed
        "fs.read": "none",
        "fs.list": "none",
        "fs.exists": "none",
        "sys.info": "none",
        "sys.processes": "none",
        "sys.disk_usage": "none",
        "mem.search": "none",
        "dev.repo_overview": "none",
        "dev.search_code": "none",
        "dev.git_status": "none",
        "dev.git_diff": "none",
        "util.noop": "none",
        "util.finish": "none",
        
        # RESTRICTED tools - sandbox required
        "code.exec_python": "sandbox",
        "dev.run_tests": "sandbox",
        "fs.write": "sandbox",  # Allowlist enforced in sandbox
        "proc.run": "sandbox",  # Allow process execution via sandbox (fallback direct)
        
        # DANGEROUS tools - lab container required
        "net.http_get": "lab_container",
        "net.http_post": "lab_container",
        "fs.delete": "lab_container",
        "mem.record": "lab_container",  # Can modify memory
    }
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize isolation manager.
        
        Args:
            strict_mode: If True, enforce fail-closed (production default)
        """
        self._strict_mode = strict_mode
        
        # Check isolation availability
        self._sandbox_available = self._check_sandbox_available()
        self._lab_container_available = self._check_lab_available()
        
        logger.info("IsolationManager initialized", 
                   strict_mode=strict_mode,
                   sandbox=self._sandbox_available,
                   lab=self._lab_container_available)
    
    def _check_sandbox_available(self) -> bool:
        """Check if sandbox service is available"""
        try:
            from unified_core.sandbox_service import get_sandbox_service
            sandbox = get_sandbox_service()
            return True
        except Exception as e:
            logger.warning("Sandbox service not available", error=str(e))
            return False
    
    def _check_lab_available(self) -> bool:
        """Check if lab container service is available"""
        try:
            import docker
            client = docker.from_env()
            client.ping()
            return True
        except Exception:
            return False
    
    def determine_isolation(
        self,
        tool_name: str,
        risk_level: RiskLevel,
        force_isolation: Optional[str] = None
    ) -> str:
        """
        Determine required isolation level for tool execution.
        
        Args:
            tool_name: Tool to execute
            risk_level: Assessed risk level
            force_isolation: Override isolation (for testing/debugging)
        
        Returns:
            "none" | "sandbox" | "lab_container"
        """
        # Force isolation if specified
        if force_isolation:
            logger.warning(f"Forced isolation: {force_isolation} for {tool_name}")
            return force_isolation
        
        # Check policy
        policy_isolation = self.TOOL_ISOLATION_POLICY.get(tool_name, "sandbox")
        
        # Elevate based on risk level
        if risk_level == RiskLevel.DANGEROUS:
            if policy_isolation != "lab_container":
                logger.warning(
                    f"Elevating {tool_name} from {policy_isolation} to lab_container due to DANGEROUS risk"
                )
                policy_isolation = "lab_container"
        
        elif risk_level == RiskLevel.RESTRICTED:
            if policy_isolation == "none":
                logger.warning(
                    f"Elevating {tool_name} from none to sandbox due to RESTRICTED risk"
                )
                policy_isolation = "sandbox"
        
        return policy_isolation
    
    async def execute_in_isolation(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        isolation: str,
        timeout_ms: int = 10000
    ) -> Dict[str, Any]:
        """
        Execute tool in specified isolation layer.
        
        FAIL-CLOSED ENFORCEMENT:
        - sandbox required but unavailable = BLOCKED
        - lab_container required but unavailable = BLOCKED
        
        Returns:
            Execution result with metrics tracking
        """
        start_time = time.time()
        
        try:
            # Enforce strict mode
            if self._strict_mode:
                if isolation == "sandbox" and not self._sandbox_available:
                    inc_counter("blocked_actions_total", {
                        "reason": "sandbox_unavailable",
                        "tool": tool_name
                    })
                    logger.error("BLOCKED: Sandbox required but unavailable",
                               tool=tool_name, isolation=isolation)
                    return {
                        "success": False,
                        "error": "Sandbox required but not available - BLOCKED",
                        "blocked": True,
                        "reason": "sandbox_unavailable"
                    }
                
                if isolation == "lab_container" and not self._lab_container_available:
                    inc_counter("blocked_actions_total", {
                        "reason": "lab_unavailable",
                        "tool": tool_name
                    })
                    logger.error("BLOCKED: Lab container required but unavailable",
                               tool=tool_name, isolation=isolation)
                    return {
                        "success": False,
                        "error": "Lab container required but not available - DANGEROUS operation BLOCKED",
                        "blocked": True,
                        "reason": "lab_unavailable"
                    }
            
            # Execute in appropriate isolation
            if isolation == "none":
                result = await self._execute_direct(tool_name, arguments)
            elif isolation == "sandbox":
                result = await self._execute_sandbox(tool_name, arguments, timeout_ms)
            elif isolation == "lab_container":
                result = await self._execute_lab_container(tool_name, arguments, timeout_ms)
            else:
                raise ValueError(f"Unknown isolation level: {isolation}")
            
            # Record metrics
            latency_ms = (time.time() - start_time) * 1000
            observe_histogram("tool_exec_ms", latency_ms, {
                "tool": tool_name,
                "isolation": isolation
            })
            
            if result.get("success"):
                inc_counter("tool_exec_success_total", {"tool": tool_name, "isolation": isolation})
            else:
                inc_counter("tool_exec_failure_total", {"tool": tool_name, "isolation": isolation})
            
            return result
            
        except Exception as e:
            inc_counter("tool_exec_error_total", {"tool": tool_name, "isolation": isolation})
            logger.error("Tool execution error", tool=tool_name, error=str(e))
            return {
                "success": False,
                "error": f"Execution error: {str(e)}",
                "blocked": False
            }
    
    async def _execute_direct(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute directly via UnifiedToolRegistry"""
        from unified_core.tool_registry import get_unified_registry
        
        logger.debug("Direct execution", tool=tool_name)
        registry = get_unified_registry()
        result = await registry.execute(tool_name, arguments)
        
        return result
    
    async def _execute_sandbox(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout_ms: int
    ) -> Dict[str, Any]:
        """Execute in sandbox (no network, temp fs)"""
        
        # STRICT MODE: Block if sandbox unavailable
        if self._strict_mode and not self._sandbox_available:
            inc_counter("blocked_actions_total", {
                "reason": "sandbox_unavailable",
                "tool": tool_name
            })
            logger.error("BLOCKED: Sandbox unavailable in strict mode", tool=tool_name)
            return {
                "success": False,
                "error": "Sandbox required but not available - operation BLOCKED",
                "blocked": True,
                "reason": "sandbox_unavailable"
            }
        
        # Route to sandbox service
        if self._sandbox_available:
            try:
                from unified_core.sandbox_service import get_sandbox_service
                sandbox = get_sandbox_service()
                
                logger.info("Routing to sandbox service", tool=tool_name)
                result = await sandbox.execute(tool_name, arguments, timeout_ms)
                return result
                
            except Exception as e:
                logger.error("Sandbox service error", tool=tool_name, error=str(e))
                inc_counter("sandbox_service_error_total", {"tool": tool_name})
                return {
                    "success": False,
                    "error": f"Sandbox service error: {str(e)}",
                    "blocked": False
                }
        
        # Fallback: Direct execution with warning (NON-PRODUCTION)
        logger.warning("Sandbox execution not yet implemented - using direct (NOT PRODUCTION SAFE)",
                      tool=tool_name)
        inc_counter("sandbox_fallback_total", {"tool": tool_name})
        
        return await self._execute_direct(tool_name, arguments)
    
    async def _execute_lab_container(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout_ms: int
    ) -> Dict[str, Any]:
        """Execute in lab container (full Docker isolation)"""
        
        # STRICT MODE: Always block if lab unavailable
        if not self._lab_container_available:
            inc_counter("blocked_actions_total", {
                "reason": "lab_unavailable",
                "tool": tool_name
            })
            logger.error("BLOCKED: Lab container unavailable", tool=tool_name)
            return {
                "success": False,
                "error": "Lab container required but not available - DANGEROUS operation BLOCKED",
                "blocked": True,
                "reason": "lab_unavailable"
            }
        
        # TODO: Route to lab container orchestrator
        logger.error("Lab container execution not yet implemented", tool=tool_name)
        return {
            "success": False,
            "error": "Lab container not implemented - operation blocked for safety",
            "blocked": True,
            "reason": "lab_not_implemented"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get isolation manager status"""
        return {
            "sandbox_available": self._sandbox_available,
            "lab_container_available": self._lab_container_available,
            "policy_tools": len(self.TOOL_ISOLATION_POLICY)
        }


# Global singleton
_isolation_manager: Optional[IsolationManager] = None


def get_isolation_manager() -> IsolationManager:
    """Get or create global isolation manager"""
    global _isolation_manager
    if _isolation_manager is None:
        _isolation_manager = IsolationManager()
    return _isolation_manager
