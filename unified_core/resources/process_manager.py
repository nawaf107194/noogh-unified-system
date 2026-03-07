"""
Process Manager - Dynamic Process and GPU Memory Control
Kill low-priority processes, reallocate GPU memory
"""
import logging
import asyncio
import os
import signal
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import psutil

logger = logging.getLogger("unified_core.resources.process_manager")


class ProcessPriority(Enum):
    CRITICAL = 0  # Never kill
    HIGH = 1
    NORMAL = 2
    LOW = 3
    EXPENDABLE = 4  # Kill first


@dataclass
class ManagedProcess:
    """Process tracked by the manager."""
    pid: int
    name: str
    priority: ProcessPriority
    cpu_percent: float
    memory_mb: float
    gpu_memory_mb: float
    started_at: datetime
    owner: str  # Agent or system component
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KillDecision:
    """Decision to kill a process."""
    pid: int
    name: str
    reason: str
    memory_to_free_mb: float
    gpu_memory_to_free_mb: float
    approved: bool = False


class ProcessManager:
    """
    Dynamic process manager for resource control.
    Handles process priority, killing, and GPU memory reallocation.
    """
    
    # Processes that should never be killed
    PROTECTED_NAMES = {
        "systemd", "init", "kernel", "kworker",
        "sshd", "bash", "python", "postgres",
        "redis-server", "dockerd", "containerd"
    }
    
    # GPU process names (will try to shrink before killing)
    GPU_PROCESS_NAMES = {
        "python", "python3", "jupyter", "nvidia-smi",
        "torch", "tensorflow", "cuda"
    }
    
    def __init__(
        self,
        kill_approval_callback: Optional[Callable[[KillDecision], bool]] = None,
        auto_kill_expendable: bool = True
    ):
        self.kill_approval_callback = kill_approval_callback
        self.auto_kill_expendable = auto_kill_expendable
        
        self._managed_processes: Dict[int, ManagedProcess] = {}
        self._priority_overrides: Dict[int, ProcessPriority] = {}
        self._protected_pids: Set[int] = {os.getpid()}
        
        self._nvml_initialized = False
        self._kill_history: List[Dict[str, Any]] = []
    
    async def initialize(self):
        """Initialize process manager."""
        # Initialize NVML for GPU memory management
        try:
            import pynvml
            pynvml.nvmlInit()
            self._nvml_initialized = True
            logger.info("ProcessManager: NVML initialized")
        except ImportError:
            logger.warning("pynvml not available, GPU memory management disabled")
        except Exception as e:
            logger.warning(f"NVML init failed: {e}")
        
        # Protect our own PID and parent
        self._protected_pids.add(os.getpid())
        self._protected_pids.add(os.getppid())
    
    def set_priority(self, pid: int, priority: ProcessPriority):
        """Set priority for a specific process."""
        self._priority_overrides[pid] = priority
        logger.info(f"PID {pid} priority set to {priority.name}")
    
    def protect(self, pid: int):
        """Add PID to protected list."""
        self._protected_pids.add(pid)
    
    def unprotect(self, pid: int):
        """Remove PID from protected list."""
        self._protected_pids.discard(pid)
    
    def register_process(
        self,
        pid: int,
        owner: str,
        priority: ProcessPriority = ProcessPriority.NORMAL,
        metadata: Optional[Dict] = None
    ):
        """Register a managed process."""
        try:
            proc = psutil.Process(pid)
            with proc.oneshot():
                managed = ManagedProcess(
                    pid=pid,
                    name=proc.name(),
                    priority=priority,
                    cpu_percent=proc.cpu_percent(),
                    memory_mb=proc.memory_info().rss / (1024 * 1024),
                    gpu_memory_mb=0.0,  # Will be updated separately
                    started_at=datetime.fromtimestamp(proc.create_time()),
                    owner=owner,
                    metadata=metadata or {}
                )
                self._managed_processes[pid] = managed
                self._priority_overrides[pid] = priority
                logger.info(f"Registered process: {pid} ({proc.name()}) priority={priority.name}")
        except psutil.NoSuchProcess:
            logger.warning(f"Process {pid} not found")
    
    def get_all_processes(
        self,
        sort_by: str = "memory",
        descending: bool = True
    ) -> List[ManagedProcess]:
        """Get all processes with resource usage."""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info', 'create_time']):
            try:
                info = proc.info
                pid = info['pid']
                
                # Get priority
                priority = self._priority_overrides.get(pid)
                if priority is None:
                    priority = self._infer_priority(info['name'], pid)
                
                managed = ManagedProcess(
                    pid=pid,
                    name=info['name'] or "unknown",
                    priority=priority,
                    cpu_percent=info['cpu_percent'] or 0.0,
                    memory_mb=(info['memory_info'].rss if info['memory_info'] else 0) / (1024 * 1024),
                    gpu_memory_mb=0.0,
                    started_at=datetime.fromtimestamp(info['create_time']) if info['create_time'] else datetime.now(),
                    owner="system"
                )
                processes.append(managed)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort
        sort_key = {
            "memory": lambda p: p.memory_mb,
            "cpu": lambda p: p.cpu_percent,
            "priority": lambda p: p.priority.value,
            "started": lambda p: p.started_at.timestamp()
        }.get(sort_by, lambda p: p.memory_mb)
        
        return sorted(processes, key=sort_key, reverse=descending)
    
    def _infer_priority(self, name: str, pid: int) -> ProcessPriority:
        """Infer process priority from name and context."""
        if pid in self._protected_pids:
            return ProcessPriority.CRITICAL
        
        name_lower = name.lower() if name else ""
        
        # Critical system processes
        if any(p in name_lower for p in self.PROTECTED_NAMES):
            return ProcessPriority.CRITICAL
        
        # High priority for databases, servers
        if any(p in name_lower for p in ["postgres", "redis", "nginx", "docker"]):
            return ProcessPriority.HIGH
        
        # GPU processes are important
        if any(p in name_lower for p in self.GPU_PROCESS_NAMES):
            return ProcessPriority.HIGH
        
        return ProcessPriority.NORMAL
    
    async def free_memory(
        self,
        target_mb: float,
        include_gpu: bool = False
    ) -> Dict[str, Any]:
        """
        Free up memory by killing low-priority processes.
        Returns summary of actions taken.
        """
        freed_ram_mb = 0.0
        freed_gpu_mb = 0.0
        killed = []
        
        # Get processes sorted by priority (expendable first) then by memory
        processes = self.get_all_processes(sort_by="memory")
        
        # Sort by priority value descending (EXPENDABLE=4 first)
        processes.sort(key=lambda p: (p.priority.value, p.memory_mb), reverse=True)
        
        for proc in processes:
            if freed_ram_mb >= target_mb:
                break
            
            if proc.priority == ProcessPriority.CRITICAL:
                continue
            
            if proc.pid in self._protected_pids:
                continue
            
            # Create kill decision
            decision = KillDecision(
                pid=proc.pid,
                name=proc.name,
                reason=f"Freeing memory (need {target_mb}MB, freed {freed_ram_mb:.1f}MB)",
                memory_to_free_mb=proc.memory_mb,
                gpu_memory_to_free_mb=proc.gpu_memory_mb
            )
            
            # Check approval
            if proc.priority == ProcessPriority.EXPENDABLE and self.auto_kill_expendable:
                decision.approved = True
            elif self.kill_approval_callback:
                decision.approved = self.kill_approval_callback(decision)
            else:
                decision.approved = proc.priority.value >= ProcessPriority.LOW.value
            
            if decision.approved:
                success = await self._kill_process(proc.pid, graceful=True)
                if success:
                    freed_ram_mb += proc.memory_mb
                    if include_gpu:
                        freed_gpu_mb += proc.gpu_memory_mb
                    killed.append({
                        "pid": proc.pid,
                        "name": proc.name,
                        "memory_mb": proc.memory_mb
                    })
        
        result = {
            "success": freed_ram_mb >= target_mb,
            "target_mb": target_mb,
            "freed_ram_mb": freed_ram_mb,
            "freed_gpu_mb": freed_gpu_mb,
            "killed_processes": killed
        }
        
        logger.info(f"Memory free result: {result}")
        return result
    
    async def _kill_process(
        self,
        pid: int,
        graceful: bool = True,
        timeout: float = 5.0
    ) -> bool:
        """Kill a process, gracefully if possible."""
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            
            if graceful:
                # Try SIGTERM first
                proc.terminate()
                try:
                    proc.wait(timeout=timeout)
                    logger.info(f"Gracefully terminated {pid} ({name})")
                    self._record_kill(pid, name, "SIGTERM")
                    return True
                except psutil.TimeoutExpired:
                    pass
            
            # Force kill
            proc.kill()
            proc.wait(timeout=2.0)
            logger.info(f"Force killed {pid} ({name})")
            self._record_kill(pid, name, "SIGKILL")
            return True
            
        except psutil.NoSuchProcess:
            return True  # Already dead
        except psutil.AccessDenied:
            logger.error(f"Access denied killing {pid}")
            return False
        except Exception as e:
            logger.error(f"Failed to kill {pid}: {e}")
            return False
    
    def _record_kill(self, pid: int, name: str, signal_type: str):
        """Record kill action for audit."""
        self._kill_history.append({
            "pid": pid,
            "name": name,
            "signal": signal_type,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep last 1000 entries
        if len(self._kill_history) > 1000:
            self._kill_history.pop(0)
    
    async def reallocate_gpu_memory(
        self,
        target_gpu: int = 0,
        target_free_mb: float = 1000
    ) -> Dict[str, Any]:
        """
        Attempt to free GPU memory by terminating GPU processes.
        """
        if not self._nvml_initialized:
            return {"success": False, "error": "NVML not available"}
        
        try:
            import pynvml
            
            handle = pynvml.nvmlDeviceGetHandleByIndex(target_gpu)
            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            
            current_free_mb = memory.free / (1024 * 1024)
            if current_free_mb >= target_free_mb:
                return {
                    "success": True,
                    "current_free_mb": current_free_mb,
                    "message": "Already have enough free GPU memory"
                }
            
            # Get GPU processes
            processes = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
            
            killed = []
            for proc in processes:
                if current_free_mb >= target_free_mb:
                    break
                
                pid = proc.pid
                if pid in self._protected_pids:
                    continue
                
                priority = self._priority_overrides.get(pid, ProcessPriority.NORMAL)
                if priority == ProcessPriority.CRITICAL:
                    continue
                
                proc_memory_mb = proc.usedGpuMemory / (1024 * 1024)
                
                decision = KillDecision(
                    pid=pid,
                    name=f"GPU Process {pid}",
                    reason=f"Freeing GPU memory (need {target_free_mb}MB)",
                    memory_to_free_mb=0,
                    gpu_memory_to_free_mb=proc_memory_mb
                )
                
                if self.kill_approval_callback:
                    decision.approved = self.kill_approval_callback(decision)
                else:
                    decision.approved = priority.value >= ProcessPriority.LOW.value
                
                if decision.approved:
                    success = await self._kill_process(pid, graceful=True)
                    if success:
                        current_free_mb += proc_memory_mb
                        killed.append({"pid": pid, "gpu_memory_mb": proc_memory_mb})
            
            return {
                "success": current_free_mb >= target_free_mb,
                "freed_gpu_mb": sum(k["gpu_memory_mb"] for k in killed),
                "current_free_mb": current_free_mb,
                "killed_processes": killed
            }
            
        except Exception as e:
            logger.error(f"GPU memory reallocation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_kill_history(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get kill history."""
        if last_n:
            return self._kill_history[-last_n:]
        return self._kill_history.copy()
