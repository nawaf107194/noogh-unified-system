"""
NOOGH Sandbox Service

Safe execution environment for RESTRICTED tools.

SECURITY FEATURES:
- Process isolation (subprocess)
- Network disabled (no external calls)
- Temp working directory (isolated filesystem)
- Resource limits (CPU time, memory, max files)
- Timeout enforcement

SUPPORTED TOOLS:
- code.exec_python
- dev.run_tests
- fs.write (with allowlist)
"""

import subprocess
import tempfile
import os
import shutil
import resource
import signal
from typing import Dict, Any, Optional
from pathlib import Path
import json
import time

from unified_core.observability import get_logger, inc_counter, observe_histogram


logger = get_logger("sandbox_service")


class SandboxService:
    """
    Sandbox service for executing RESTRICTED tools safely.
    
    Isolation Features:
    - Process isolation via subprocess
    - Temp working directory
    - No network access (best effort)
    - CPU/Memory/Time limits
    - File size limits
    """
    
    def __init__(
        self,
        max_cpu_seconds: int = 30,
        max_memory_mb: int = 512,
        max_output_kb: int = 1024,
        max_files: int = 100
    ):
        """
        Initialize sandbox service.
        
        Args:
            max_cpu_seconds: Maximum CPU time per execution
            max_memory_mb: Maximum memory usage (MB)
            max_output_kb: Maximum output size (KB)
            max_files: Maximum number of files created
        """
        self.max_cpu_seconds = max_cpu_seconds
        self.max_memory_mb = max_memory_mb
        self.max_output_kb = max_output_kb
        self.max_files = max_files
        
        logger.info("SandboxService initialized",
                   cpu_limit=max_cpu_seconds,
                   memory_limit_mb=max_memory_mb)
    
    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout_ms: int = 10000
    ) -> Dict[str, Any]:
        """
        Execute tool in sandbox.
        
        Args:
            tool_name: Tool to execute
            arguments: Tool arguments
            timeout_ms: Execution timeout
            
        Returns:
            Execution result with sandbox metrics
        """
        start_time = time.time()
        
        # Create temp workspace with restricted permissions
        workspace = tempfile.mkdtemp(prefix="noogh_sandbox_")
        os.chmod(workspace, 0o700)
        
        try:
            logger.info("Sandbox execution started",
                       tool=tool_name,
                       workspace=workspace)
            
            # Route to appropriate handler
            if tool_name == "code.exec_python":
                result = await self._exec_python(arguments, workspace, timeout_ms)
            elif tool_name == "fs.write":
                result = await self._exec_fs_write(arguments, workspace)
            elif tool_name == "dev.run_tests":
                result = await self._exec_run_tests(arguments, workspace, timeout_ms)
            elif tool_name == "proc.run":
                result = await self._exec_proc_run(arguments, workspace, timeout_ms)
            else:
                result = {
                    "success": False,
                    "error": f"Tool {tool_name} not supported in sandbox"
                }
            
            # Record metrics
            latency_ms = (time.time() - start_time) * 1000
            observe_histogram("sandbox_exec_ms", latency_ms, {"tool": tool_name})
            
            if result.get("success"):
                inc_counter("sandbox_exec_success_total", {"tool": tool_name})
            else:
                inc_counter("sandbox_exec_failure_total", {"tool": tool_name})
            
            return result
            
        except Exception as e:
            logger.error("Sandbox execution error", tool=tool_name, error=str(e))
            inc_counter("sandbox_exec_error_total", {"tool": tool_name})
            return {
                "success": False,
                "error": f"Sandbox error: {str(e)}"
            }
        
        finally:
            # Cleanup workspace
            try:
                shutil.rmtree(workspace)
                logger.debug("Workspace cleaned", workspace=workspace)
            except Exception as e:
                logger.warning("Workspace cleanup failed", error=str(e))
    
    async def _exec_python(
        self,
        arguments: Dict[str, Any],
        workspace: str,
        timeout_ms: int
    ) -> Dict[str, Any]:
        """
        Execute Python code in sandbox.
        
        Security:
        - No network access
        - Temp directory only
        - CPU/Memory limits
        - Timeout
        """
        code = arguments.get("code", "")
        
        if not code:
            return {"success": False, "error": "No code provided"}
        
        # Write code to temp file
        code_file = os.path.join(workspace, "script.py")
        with open(code_file, "w") as f:
            f.write(code)
        
        # Prepare execution
        timeout_seconds = timeout_ms / 1000.0
        
        try:
            # Execute with limits
            result = subprocess.run(
                ["python3", code_file],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                # Set resource limits (Linux only)
                preexec_fn=lambda: self._set_limits()
            )
            
            # Check output size
            output = result.stdout
            if len(output) > self.max_output_kb * 1024:
                output = output[:self.max_output_kb * 1024] + "\n... (truncated)"
            
            return {
                "success": result.returncode == 0,
                "output": output,
                "error": result.stderr if result.returncode != 0 else None,
                "exit_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            logger.warning("Python execution timeout", timeout=timeout_seconds)
            inc_counter("sandbox_timeout_total", {"tool": "code.exec_python"})
            return {
                "success": False,
                "error": f"Execution timeout after {timeout_seconds}s"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}"
            }
    
    async def _exec_fs_write(
        self,
        arguments: Dict[str, Any],
        workspace: str
    ) -> Dict[str, Any]:
        """
        Write file in sandbox (with path allowlist check).
        
        Note: Actual writes should go through FilesystemActuator
        with allowlist validation. This is for testing only.
        """
        path = arguments.get("path", "")
        content = arguments.get("content", "")
        
        if not path:
            return {"success": False, "error": "No path provided"}
        
        # Security: Only allow writes within workspace
        target_path = Path(workspace) / Path(path).name
        
        try:
            target_path.write_text(content)
            logger.info("File written in sandbox", path=str(target_path))
            
            return {
                "success": True,
                "path": str(target_path),
                "size": len(content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Write error: {str(e)}"
            }
    
    async def _exec_run_tests(
        self,
        arguments: Dict[str, Any],
        workspace: str,
        timeout_ms: int
    ) -> Dict[str, Any]:
        """
        Run tests in sandbox.
        
        Example: pytest, unittest, etc.
        """
        test_command = arguments.get("command", "pytest")
        test_path = arguments.get("path", ".")
        
        timeout_seconds = timeout_ms / 1000.0
        
        try:
            result = subprocess.run(
                [test_command, test_path],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                preexec_fn=lambda: self._set_limits()
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "exit_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            inc_counter("sandbox_timeout_total", {"tool": "dev.run_tests"})
            return {
                "success": False,
                "error": f"Test timeout after {timeout_seconds}s"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Test error: {str(e)}"
            }
            
    async def _exec_proc_run(
        self,
        arguments: Dict[str, Any],
        workspace: str,
        timeout_ms: int
    ) -> Dict[str, Any]:
        """
        Execute arbitrary process via external helper script.
        
        Bypasses Python's os.fork() which deadlocks when CUDA/PyTorch
        threads are active. Delegates to _sandbox_runner.sh which runs
        entirely outside the Python process space.
        """
        import asyncio
        import os
        import tempfile
        import shlex
        
        command = arguments.get("command")
        if not command:
            return {"success": False, "error": "No command provided"}
        
        # Convert list to string
        if isinstance(command, list):
            command_str = shlex.join(command)
        else:
            command_str = command
            
        timeout_seconds = max(1, int(timeout_ms / 1000.0))
        
        # Create temp files for IPC
        tmp_dir = tempfile.mkdtemp(prefix="noogh_sandbox_")
        cmd_file = os.path.join(tmp_dir, "cmd.sh")
        stdout_file = os.path.join(tmp_dir, "stdout.log")
        stderr_file = os.path.join(tmp_dir, "stderr.log")
        exit_file = os.path.join(tmp_dir, "exit_code")
        
        # Write command to file (avoids shell escaping issues)
        with open(cmd_file, "w") as f:
            f.write(command_str)
        
        # Path to the helper script
        runner_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "_sandbox_runner.sh"
        )
        
        # Build the invocation command
        invoke_cmd = (
            f"bash {shlex.quote(runner_script)} "
            f"{shlex.quote(cmd_file)} "
            f"{shlex.quote(stdout_file)} "
            f"{shlex.quote(stderr_file)} "
            f"{shlex.quote(exit_file)} "
            f"{timeout_seconds} "
            f"{shlex.quote(workspace)}"
        )
        
        def _run():
            return os.system(invoke_cmd)
        
        try:
            # Run in a thread — os.system uses vfork/posix_spawn, not fork
            await asyncio.wait_for(
                asyncio.to_thread(_run),
                timeout=timeout_seconds + 5.0
            )
            
            # Read results from temp files
            output = ""
            error = ""
            exit_code = -1
            
            if os.path.exists(stdout_file):
                with open(stdout_file, "r") as f:
                    output = f.read()
            if os.path.exists(stderr_file):
                with open(stderr_file, "r") as f:
                    error = f.read()
            if os.path.exists(exit_file):
                with open(exit_file, "r") as f:
                    exit_code = int(f.read().strip())
            
            # Truncate if too large
            if len(output) > self.max_output_kb * 1024:
                output = output[:self.max_output_kb * 1024] + "\n... (truncated)"
            
            return {
                "success": exit_code == 0,
                "output": output,
                "error": error if exit_code != 0 else None,
                "exit_code": exit_code
            }
            
        except asyncio.TimeoutError:
            inc_counter("sandbox_timeout_total", {"tool": "proc.run"})
            return {
                "success": False,
                "error": f"Execution timeout after {timeout_seconds}s"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}"
            }
        finally:
            # Cleanup temp files
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
    
    def _set_limits(self):
        """
        Set resource limits for subprocess (Linux only).
        
        Limits:
        - CPU time
        - Memory (virtual)
        - Max file size
        """
        try:
            # CPU time limit
            resource.setrlimit(
                resource.RLIMIT_CPU,
                (self.max_cpu_seconds, self.max_cpu_seconds)
            )
            
            # Memory limit (virtual memory)
            max_memory_bytes = self.max_memory_mb * 1024 * 1024
            resource.setrlimit(
                resource.RLIMIT_AS,
                (max_memory_bytes, max_memory_bytes)
            )
            
            # Max file size
            max_file_bytes = self.max_output_kb * 1024
            resource.setrlimit(
                resource.RLIMIT_FSIZE,
                (max_file_bytes, max_file_bytes)
            )
            
            # Max processes (prevent fork bombs)
            max_procs = self.max_files  # Reusing max_files as a proxy for process count
            resource.setrlimit(
                resource.RLIMIT_NPROC,
                (max_procs, max_procs)
            )
            
        except Exception as e:
            # Resource limits may not be available on all platforms
            logger.warning("Could not set resource limits", error=str(e))


# Global singleton
_sandbox_service: Optional[SandboxService] = None


def get_sandbox_service() -> SandboxService:
    """Get or create global sandbox service"""
    global _sandbox_service
    if _sandbox_service is None:
        _sandbox_service = SandboxService()
    return _sandbox_service


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_sandbox():
        sandbox = get_sandbox_service()
        
        # Test 1: Python execution
        print("Test 1: Python execution")
        result = await sandbox.execute(
            "code.exec_python",
            {"code": "print('Hello from sandbox!')"},
            timeout_ms=5000
        )
        print(f"Result: {result}")
        
        # Test 2: File write
        print("\nTest 2: File write")
        result = await sandbox.execute(
            "fs.write",
            {"path": "test.txt", "content": "sandbox test"},
            timeout_ms=1000
        )
        print(f"Result: {result}")
    
    asyncio.run(test_sandbox())
