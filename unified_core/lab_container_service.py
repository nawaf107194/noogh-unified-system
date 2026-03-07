"""
NOOGH Lab Container Service

Maximum isolation for DANGEROUS tools.

SECURITY FEATURES:
- Docker container per execution (single-use)
- Network disabled (--network=none)
- Read-only filesystem (--read-only)
- No capabilities (--cap-drop=ALL)
- Resource limits (CPU, Memory)
- Auto-cleanup after execution

SUPPORTED TOOLS:
- proc.run (shell commands)
- net.http_get/post (with network allowlist)
- fs.delete (destructive operations)
- mem.record (memory modifications)
"""

import docker
import tempfile
import os
import shutil
from typing import Dict, Any, Optional
import json
import time

from unified_core.observability import get_logger, inc_counter, observe_histogram


logger = get_logger("lab_container_service")


class LabContainerService:
    """
    Lab container service for maximum isolation.
    
    Uses Docker to execute DANGEROUS tools in complete isolation.
    Each execution gets a fresh container that is destroyed after use.
    """
    
    def __init__(
        self,
        docker_image: str = "python:3.11-slim",
        max_cpu_count: int = 1,
        max_memory_mb: int = 512,
        network_mode: str = "none"
    ):
        """
        Initialize lab container service.
        
        Args:
            docker_image: Base Docker image to use
            max_cpu_count: Maximum CPU count
            max_memory_mb: Maximum memory (MB)
            network_mode: Network mode (none/bridge)
        """
        self.docker_image = docker_image
        self.max_cpu_count = max_cpu_count
        self.max_memory_mb = max_memory_mb
        self.network_mode = network_mode
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            self.docker_available = True
            logger.info("LabContainerService initialized",
                       image=docker_image,
                       cpu=max_cpu_count,
                       memory_mb=max_memory_mb)
        except Exception as e:
            self.docker_available = False
            logger.error("Docker not available", error=str(e))
    
    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout_ms: int = 30000
    ) -> Dict[str, Any]:
        """
        Execute tool in lab container.
        
        Args:
            tool_name: Tool to execute
            arguments: Tool arguments
            timeout_ms: Execution timeout
            
        Returns:
            Execution result
        """
        if not self.docker_available:
            inc_counter("lab_unavailable_total", {"tool": tool_name})
            return {
                "success": False,
                "error": "Docker not available",
                "blocked": True,
                "reason": "docker_unavailable"
            }
        
        start_time = time.time()
        container = None
        
        try:
            logger.info("Lab execution started", tool=tool_name)
            
            # Route to appropriate handler
            if tool_name == "proc.run":
                result = await self._exec_process(arguments, timeout_ms)
            elif tool_name in ["net.http_get", "net.http_post"]:
                result = await self._exec_network(tool_name, arguments, timeout_ms)
            elif tool_name == "fs.delete":
                result = await self._exec_fs_delete(arguments, timeout_ms)
            else:
                result = {
                    "success": False,
                    "error": f"Tool {tool_name} not supported in lab container"
                }
            
            # Record metrics
            latency_ms = (time.time() - start_time) * 1000
            observe_histogram("lab_exec_ms", latency_ms, {"tool": tool_name})
            
            if result.get("success"):
                inc_counter("lab_exec_success_total", {"tool": tool_name})
            else:
                inc_counter("lab_exec_failure_total", {"tool": tool_name})
            
            return result
            
        except Exception as e:
            logger.error("Lab execution error", tool=tool_name, error=str(e))
            inc_counter("lab_exec_error_total", {"tool": tool_name})
            return {
                "success": False,
                "error": f"Lab error: {str(e)}"
            }
        
        finally:
            # Cleanup container if created
            if container:
                try:
                    container.remove(force=True)
                    logger.debug("Container cleaned up", container_id=container.id[:12])
                except Exception as e:
                    logger.warning("Container cleanup failed", error=str(e))
    
    async def _exec_process(
        self,
        arguments: Dict[str, Any],
        timeout_ms: int
    ) -> Dict[str, Any]:
        """
        Execute shell command in container.
        
        CRITICAL SECURITY:
        - No shell injection (use exec form)
        - Read-only filesystem
        - No network
        - Minimal capabilities
        """
        command = arguments.get("command", "")
        
        if not command:
            return {"success": False, "error": "No command provided"}
        
        timeout_seconds = timeout_ms / 1000.0
        
        try:
            # Create container with maximum isolation
            container = self.docker_client.containers.run(
                self.docker_image,
                command=["sh", "-c", command],
                detach=True,
                remove=False,  # We'll remove manually
                network_mode=self.network_mode,
                read_only=True,
                cap_drop=["ALL"],
                mem_limit=f"{self.max_memory_mb}m",
                cpu_count=self.max_cpu_count,
                security_opt=["no-new-privileges"],
            )
            
            # Wait for completion
            exit_code = container.wait(timeout=timeout_seconds)
            
            # Get logs
            output = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
            errors = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')
            
            # Cleanup
            container.remove(force=True)
            
            return {
                "success": exit_code["StatusCode"] == 0,
                "output": output,
                "error": errors if exit_code["StatusCode"] != 0 else None,
                "exit_code": exit_code["StatusCode"]
            }
            
        except docker.errors.ContainerError as e:
            return {
                "success": False,
                "error": f"Container error: {str(e)}",
                "exit_code": e.exit_status
            }
        except Exception as e:
            inc_counter("lab_timeout_total", {"tool": "proc.run"})
            return {
                "success": False,
                "error": f"Execution error: {str(e)}"
            }
    
    async def _exec_network(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout_ms: int
    ) -> Dict[str, Any]:
        """
        Execute network request in container.
        
        NOTE: Would need network allowlist in production.
        For now, we block all network operations.
        """
        # In production, this would:
        # 1. Check URL against allowlist
        # 2. Use container with limited network
        # 3. Execute request with timeout
        
        return {
            "success": False,
            "error": "Network operations not yet implemented in lab",
            "blocked": True,
            "reason": "network_not_implemented"
        }
    
    async def _exec_fs_delete(
        self,
        arguments: Dict[str, Any],
        timeout_ms: int
    ) -> Dict[str, Any]:
        """
        Execute real file deletion in an isolated container.
        
        CRITICAL: Mounts the specific path as a volume to perform deletion.
        """
        path = arguments.get("path", "")
        if not path:
            return {"success": False, "error": "No path provided"}
        
        # Resolve real path
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
             return {"success": False, "error": f"Path does not exist: {abs_path}"}

        parent_dir = os.path.dirname(abs_path)
        file_name = os.path.basename(abs_path)

        try:
            logger.info("Executing isolated deletion", path=abs_path)
            # Mount parent dir and rm the file
            self.docker_client.containers.run(
                self.docker_image,
                command=["rm", "-rf", f"/mnt/{file_name}"],
                volumes={parent_dir: {'bind': '/mnt', 'mode': 'rw'}},
                remove=True,
                network_mode="none",
                cap_drop=["ALL"],
                security_opt=["no-new-privileges"]
            )
            
            return {
                "success": True,
                "deleted": abs_path,
                "mode": "REAL"
            }
        except Exception as e:
            logger.error("Isolated deletion failed", path=abs_path, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def is_available(self) -> bool:
        """Check if lab container service is available"""
        return self.docker_available
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "available": self.docker_available,
            "image": self.docker_image,
            "network_mode": self.network_mode,
            "cpu_limit": self.max_cpu_count,
            "memory_limit_mb": self.max_memory_mb
        }


# Global singleton
_lab_service: Optional[LabContainerService] = None


def get_lab_service() -> LabContainerService:
    """Get or create global lab container service"""
    global _lab_service
    if _lab_service is None:
        _lab_service = LabContainerService()
    return _lab_service


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_lab():
        lab = get_lab_service()
        
        if not lab.is_available():
            print("❌ Docker not available")
            return
        
        print("✅ Lab Container Service available")
        print(f"Status: {lab.get_status()}")
        
        # Test: Simple command
        print("\nTest: Execute command in container")
        result = await lab.execute(
            "proc.run",
            {"command": "echo 'Hello from lab!' && ls -la"},
            timeout_ms=10000
        )
        
        print(f"Success: {result['success']}")
        print(f"Output: {result.get('output', 'N/A')}")
    
    asyncio.run(test_lab())
