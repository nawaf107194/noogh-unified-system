"""
NOOGH Resource Manager

Manages GPU tokens, file locks, and tool rate limits.

SECURITY: Prevents resource exhaustion attacks and concurrent access conflicts.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional, Set

logger = logging.getLogger("unified_core.orchestration.resource_manager")


@dataclass
class ResourceQuota:
    """Resource quotas per task"""
    gpu_level: str = "none"  # none | low | medium | high
    max_file_locks: int = 5
    max_time_ms: int = 30000
    max_tools_per_task: int = 1


class ResourceManager:
    """
    Manages system resources for safe concurrent execution.
    
    Features:
    - GPU token allocation
    - File system locks
    - Tool rate limiting
    - Timeout enforcement
    """
    
    # GPU token limits (max concurrent tasks per level)
    GPU_LIMITS = {
        "none": float('inf'),
        "low": 4,
        "medium": 2,
        "high": 1
    }
    
    def __init__(self):
        # GPU tokens in use
        self._gpu_tokens: Dict[str, int] = {
            "none": 0,
            "low": 0,
            "medium": 0,
            "high": 0
        }
        
        # File locks: path → task_id
        self._file_locks: Dict[str, str] = {}
        
        # Tool rate limits: tool_name → last_used_time
        self._tool_last_used: Dict[str, float] = {}
        self._tool_min_interval_ms = 1000  # Min time between calls
        
        # Active tasks: task_id → start_time
        self._active_tasks: Dict[str, float] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info("✅ ResourceManager initialized")
    
    async def acquire_resources(
        self,
        task_id: str,
        gpu_level: str = "none",
        fs_locks: Optional[list] = None,
        time_budget_ms: int = 30000
    ) -> tuple[bool, Optional[str]]:
        """
        Acquire resources for task execution.
        
        Returns:
            (success, error_message)
        """
        async with self._lock:
            # Check GPU availability
            if gpu_level != "none":
                limit = self.GPU_LIMITS.get(gpu_level, 0)
                if self._gpu_tokens[gpu_level] >= limit:
                    return False, f"GPU {gpu_level} tokens exhausted ({self._gpu_tokens[gpu_level]}/{limit})"
            
            # Check file locks
            if fs_locks:
                for path in fs_locks:
                    if path in self._file_locks:
                        locked_by = self._file_locks[path]
                        return False, f"Path {path} locked by task {locked_by}"
            
            # Acquire resources
            self._gpu_tokens[gpu_level] += 1
            
            if fs_locks:
                for path in fs_locks:
                    self._file_locks[path] = task_id
            
            self._active_tasks[task_id] = time.time()
            
            logger.info(f"✅ Resources acquired for task {task_id}")
            return True, None
    
    async def release_resources(
        self,
        task_id: str,
        gpu_level: str = "none",
        fs_locks: Optional[list] = None
    ):
        """Release resources after task completion"""
        async with self._lock:
            # Release GPU
            if gpu_level != "none" and self._gpu_tokens[gpu_level] > 0:
                self._gpu_tokens[gpu_level] -= 1
            
            # Release file locks
            if fs_locks:
                for path in fs_locks:
                    if self._file_locks.get(path) == task_id:
                        del self._file_locks[path]
            
            # Remove from active tasks
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]
            
            logger.info(f"✅ Resources released for task {task_id}")
    
    async def check_tool_rate_limit(self, tool_name: str) -> tuple[bool, Optional[str]]:
        """
        Check if tool can be called (rate limiting).
        
        Returns:
            (allowed, error_message)
        """
        async with self._lock:
            if tool_name in self._tool_last_used:
                last_used = self._tool_last_used[tool_name]
                elapsed_ms = (time.time() - last_used) * 1000
                
                if elapsed_ms < self._tool_min_interval_ms:
                    remaining = self._tool_min_interval_ms - elapsed_ms
                    return False, f"Tool {tool_name} rate limited. Retry in {remaining:.0f}ms"
            
            self._tool_last_used[tool_name] = time.time()
            return True, None
    
    async def check_task_timeout(self, task_id: str, max_time_ms: int) -> bool:
        """
        Check if task has exceeded time budget.
        
        Returns:
            True if timed out
        """
        async with self._lock:
            if task_id not in self._active_tasks:
                return False
            
            start_time = self._active_tasks[task_id]
            elapsed_ms = (time.time() - start_time) * 1000
            
            return elapsed_ms > max_time_ms
    
    def get_stats(self) -> Dict:
        """Get resource usage statistics"""
        return {
            "gpu_tokens": self._gpu_tokens.copy(),
            "file_locks": len(self._file_locks),
            "active_tasks": len(self._active_tasks),
            "locked_paths": list(self._file_locks.keys())
        }


# Global singleton
_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """Get or create global resource manager"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager
