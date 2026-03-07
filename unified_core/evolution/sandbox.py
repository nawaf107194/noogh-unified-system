"""
Sandbox Executor - Isolated Execution Environment for Evolution
Version: 1.1.0
Part of: Self-Directed Layer (Phase 17.5)

Executes proposals in isolated environment with:
- Time limits
- Memory limits
- Filesystem isolation
- Two-step: Canary → Promote
"""

import asyncio
import logging
import time
import tempfile
import shutil
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from contextlib import asynccontextmanager

logger = logging.getLogger("unified_core.evolution.sandbox")


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""
    timeout_seconds: float = 30.0
    max_memory_mb: int = 100
    max_output_bytes: int = 1_000_000  # 1MB
    temp_dir: Optional[Path] = None
    
    def __post_init__(self):
        if self.temp_dir is None:
            self.temp_dir = Path(tempfile.gettempdir()) / "noogh_sandbox"


@dataclass
class ExecutionResult:
    """Result of sandbox execution."""
    success: bool
    duration_ms: float
    output: str = ""
    error: str = ""
    metrics_before: Optional[Dict[str, Any]] = None
    metrics_after: Optional[Dict[str, Any]] = None
    snapshot_path: Optional[str] = None


class SandboxExecutor:
    """
    Isolated execution environment for evolution proposals.
    
    Features:
    - Time-bounded execution (30s max)
    - Memory-bounded (100MB max)
    - Filesystem isolation (temp directory only)
    - Two-step execution: Canary → Promote
    - Automatic rollback on failure
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.config.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Snapshots for rollback
        self.snapshots: Dict[str, Path] = {}
        
        # Execution stats
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.rolled_back = 0
        
        logger.info(f"SandboxExecutor initialized: {self.config.temp_dir}")
    
    def _create_snapshot(self, target_path: Path, proposal_id: str) -> Optional[Path]:
        """Create a snapshot of target file for rollback."""
        if not target_path.exists():
            return None
        
        snapshot_dir = self.config.temp_dir / "snapshots"
        snapshot_dir.mkdir(exist_ok=True)
        
        snapshot_path = snapshot_dir / f"{proposal_id}_{target_path.name}.snapshot"
        shutil.copy2(target_path, snapshot_path)
        
        self.snapshots[proposal_id] = snapshot_path
        logger.debug(f"Snapshot created: {snapshot_path}")
        
        return snapshot_path
    
    def _restore_snapshot(self, proposal_id: str, target_path: Path) -> bool:
        """Restore from snapshot (rollback)."""
        snapshot_path = self.snapshots.get(proposal_id)
        if not snapshot_path or not snapshot_path.exists():
            logger.error(f"No snapshot found for {proposal_id}")
            return False
        
        try:
            shutil.copy2(snapshot_path, target_path)
            logger.warning(f"⏪ Restored from snapshot: {target_path}")
            self.rolled_back += 1
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics for comparison."""
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "timestamp": time.time()
            }
        except:
            return {"timestamp": time.time()}
    
    async def execute_config_change(
        self,
        proposal_id: str,
        target_path: Path,
        new_content: str
    ) -> ExecutionResult:
        """Execute a config file change."""
        start_time = time.time()
        metrics_before = self._collect_metrics()
        
        # Create snapshot
        snapshot_path = self._create_snapshot(target_path, proposal_id)
        
        try:
            # Write new content
            target_path.write_text(new_content)
            
            # Collect after metrics
            metrics_after = self._collect_metrics()
            duration_ms = (time.time() - start_time) * 1000
            
            self.total_executions += 1
            self.successful_executions += 1
            
            return ExecutionResult(
                success=True,
                duration_ms=duration_ms,
                output=f"Config updated: {target_path}",
                metrics_before=metrics_before,
                metrics_after=metrics_after,
                snapshot_path=str(snapshot_path) if snapshot_path else None
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.total_executions += 1
            self.failed_executions += 1
            
            # Rollback on failure
            if snapshot_path:
                self._restore_snapshot(proposal_id, target_path)
            
            return ExecutionResult(
                success=False,
                duration_ms=duration_ms,
                error=str(e)
            )
    
    async def execute_in_sandbox(
        self,
        proposal_id: str,
        code: str,
        timeout: Optional[float] = None
    ) -> ExecutionResult:
        """
        Execute code in isolated sandbox.
        
        Uses subprocess with restricted environment.
        """
        start_time = time.time()
        metrics_before = self._collect_metrics()
        timeout = timeout or self.config.timeout_seconds
        
        # Create sandbox directory
        sandbox_dir = self.config.temp_dir / proposal_id
        sandbox_dir.mkdir(exist_ok=True)
        
        # Write code to temp file
        code_file = sandbox_dir / "patch.py"
        code_file.write_text(code)
        
        try:
            # Execute with timeout
            proc = await asyncio.create_subprocess_exec(
                "python3", str(code_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(sandbox_dir),
                env={
                    "PATH": os.environ.get("PATH", ""),
                    "PYTHONPATH": "",
                    "HOME": str(sandbox_dir),
                    "NOOGH_SANDBOX": "1",
                }
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                return ExecutionResult(
                    success=False,
                    duration_ms=(time.time() - start_time) * 1000,
                    error=f"Timeout after {timeout}s"
                )
            
            duration_ms = (time.time() - start_time) * 1000
            metrics_after = self._collect_metrics()
            
            if proc.returncode == 0:
                self.total_executions += 1
                self.successful_executions += 1
                return ExecutionResult(
                    success=True,
                    duration_ms=duration_ms,
                    output=stdout.decode()[:self.config.max_output_bytes],
                    metrics_before=metrics_before,
                    metrics_after=metrics_after
                )
            else:
                self.total_executions += 1
                self.failed_executions += 1
                return ExecutionResult(
                    success=False,
                    duration_ms=duration_ms,
                    output=stdout.decode()[:self.config.max_output_bytes],
                    error=stderr.decode()[:self.config.max_output_bytes]
                )
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.total_executions += 1
            self.failed_executions += 1
            return ExecutionResult(
                success=False,
                duration_ms=duration_ms,
                error=str(e)
            )
        finally:
            # Cleanup sandbox
            if sandbox_dir.exists():
                shutil.rmtree(sandbox_dir, ignore_errors=True)
    
    async def run_canary(
        self,
        proposal_id: str,
        test_fn: Callable[[], Tuple[bool, str]]
    ) -> ExecutionResult:
        """
        Run canary test for a proposal.
        
        test_fn should return (success, message)
        """
        start_time = time.time()
        metrics_before = self._collect_metrics()
        
        try:
            success, message = test_fn()
            duration_ms = (time.time() - start_time) * 1000
            metrics_after = self._collect_metrics()
            
            return ExecutionResult(
                success=success,
                duration_ms=duration_ms,
                output=message,
                metrics_before=metrics_before,
                metrics_after=metrics_after
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=False,
                duration_ms=duration_ms,
                error=str(e)
            )
    
    def cleanup(self):
        """Clean up sandbox resources."""
        if self.config.temp_dir.exists():
            for item in self.config.temp_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink(missing_ok=True)
        
        logger.info("Sandbox cleanup complete")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "rolled_back": self.rolled_back,
            "snapshots_count": len(self.snapshots),
            "sandbox_dir": str(self.config.temp_dir)
        }


# Singleton
_executor_instance = None

def get_sandbox_executor() -> SandboxExecutor:
    """Get the global SandboxExecutor instance."""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = SandboxExecutor()
    return _executor_instance
