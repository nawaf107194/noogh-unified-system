"""
System Resource Monitor
Real-time monitoring of CPU, RAM, GPU, Disk, and Network resources
"""
import logging
import asyncio
import os
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import psutil

logger = logging.getLogger("unified_core.resources.monitor")


@dataclass
class CPUMetrics:
    """CPU utilization metrics."""
    usage_percent: float
    usage_per_core: List[float]
    frequency_mhz: float
    frequency_max_mhz: float
    load_1m: float
    load_5m: float
    load_15m: float
    core_count: int
    thread_count: int


@dataclass
class MemoryMetrics:
    """Memory utilization metrics."""
    total_bytes: int
    available_bytes: int
    used_bytes: int
    usage_percent: float
    swap_total_bytes: int
    swap_used_bytes: int
    swap_percent: float


@dataclass
class GPUMetrics:
    """GPU utilization metrics (NVIDIA)."""
    device_id: int
    name: str
    memory_total_mb: int
    memory_used_mb: int
    memory_free_mb: int
    memory_percent: float
    gpu_utilization: float
    temperature_c: float
    power_draw_w: float
    power_limit_w: float


@dataclass
class DiskMetrics:
    """Disk utilization metrics."""
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float
    read_bytes: int
    write_bytes: int
    read_count: int
    write_count: int


@dataclass
class NetworkMetrics:
    """Network interface metrics."""
    interface: str
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errors_in: int
    errors_out: int


@dataclass
class SystemSnapshot:
    """Complete system resource snapshot."""
    timestamp: datetime
    cpu: CPUMetrics
    memory: MemoryMetrics
    gpus: List[GPUMetrics]
    disks: List[DiskMetrics]
    networks: List[NetworkMetrics]
    process_count: int
    uptime_seconds: float


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ResourceAlert:
    """Resource usage alert."""
    level: AlertLevel
    resource: str
    message: str
    value: float
    threshold: float
    timestamp: datetime


class ResourceMonitor:
    """
    Real-time system resource monitor.
    Uses psutil for CPU/RAM/Disk/Network and pynvml for GPU.
    """
    
    def __init__(
        self,
        gpu_enabled: bool = True,
        alert_callbacks: Optional[List[Callable[[ResourceAlert], None]]] = None
    ):
        self.gpu_enabled = gpu_enabled
        self.alert_callbacks = alert_callbacks or []
        
        self._nvml_initialized = False
        self._nvml_handle = None
        self._gpu_count = 0
        
        # Alert thresholds
        self.thresholds = {
            "cpu_percent": 85.0,
            "memory_percent": 90.0,
            "gpu_memory_percent": 95.0,
            "disk_percent": 90.0,
        }
        
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._history: List[SystemSnapshot] = []
        self._max_history = 1000
    
    async def initialize(self) -> bool:
        """Initialize monitoring (including GPU if available)."""
        if self.gpu_enabled:
            try:
                import pynvml
                pynvml.nvmlInit()
                self._gpu_count = pynvml.nvmlDeviceGetCount()
                self._nvml_initialized = True
                logger.info(f"NVML initialized: {self._gpu_count} GPU(s) found")
            except Exception as e:
                logger.warning(f"NVML initialization failed: {e}")
                self._nvml_initialized = False
        
        return True
    
    async def shutdown(self):
        """Cleanup NVML."""
        if self._nvml_initialized:
            try:
                import pynvml
                pynvml.nvmlShutdown()
            except Exception:
                pass
        
        if self._monitor_task:
            self._running = False
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    def get_cpu_metrics(self) -> CPUMetrics:
        """Get current CPU metrics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        load = os.getloadavg()
        
        return CPUMetrics(
            usage_percent=cpu_percent,
            usage_per_core=cpu_per_core,
            frequency_mhz=cpu_freq.current if cpu_freq else 0.0,
            frequency_max_mhz=cpu_freq.max if cpu_freq else 0.0,
            load_1m=load[0],
            load_5m=load[1],
            load_15m=load[2],
            core_count=psutil.cpu_count(logical=False) or 1,
            thread_count=psutil.cpu_count(logical=True) or 1
        )
    
    def get_memory_metrics(self) -> MemoryMetrics:
        """Get current memory metrics."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return MemoryMetrics(
            total_bytes=mem.total,
            available_bytes=mem.available,
            used_bytes=mem.used,
            usage_percent=mem.percent,
            swap_total_bytes=swap.total,
            swap_used_bytes=swap.used,
            swap_percent=swap.percent
        )
    
    def get_gpu_metrics(self) -> List[GPUMetrics]:
        """Get GPU metrics using NVML."""
        if not self._nvml_initialized:
            return []
        
        gpus = []
        try:
            import pynvml
            
            for i in range(self._gpu_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                
                memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                
                try:
                    temperature = pynvml.nvmlDeviceGetTemperature(
                        handle, pynvml.NVML_TEMPERATURE_GPU
                    )
                except Exception:
                    temperature = 0
                
                try:
                    power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                    power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000.0
                except Exception:
                    power = 0.0
                    power_limit = 0.0
                
                gpus.append(GPUMetrics(
                    device_id=i,
                    name=name,
                    memory_total_mb=memory.total // (1024 * 1024),
                    memory_used_mb=memory.used // (1024 * 1024),
                    memory_free_mb=memory.free // (1024 * 1024),
                    memory_percent=(memory.used / memory.total) * 100,
                    gpu_utilization=utilization.gpu,
                    temperature_c=temperature,
                    power_draw_w=power,
                    power_limit_w=power_limit
                ))
        except Exception as e:
            logger.error(f"Failed to get GPU metrics: {e}")
        
        return gpus
    
    def get_disk_metrics(self, paths: Optional[List[str]] = None) -> List[DiskMetrics]:
        """Get disk metrics for specified paths or all mounted disks."""
        if paths is None:
            paths = [p.mountpoint for p in psutil.disk_partitions(all=False)]
        
        disks = []
        io_counters = psutil.disk_io_counters(perdisk=True)
        
        for path in paths:
            try:
                usage = psutil.disk_usage(path)
                
                # Try to find IO stats for this disk
                read_bytes = write_bytes = read_count = write_count = 0
                for disk_name, stats in io_counters.items():
                    if disk_name in path or path in disk_name:
                        read_bytes = stats.read_bytes
                        write_bytes = stats.write_bytes
                        read_count = stats.read_count
                        write_count = stats.write_count
                        break
                
                disks.append(DiskMetrics(
                    path=path,
                    total_bytes=usage.total,
                    used_bytes=usage.used,
                    free_bytes=usage.free,
                    usage_percent=usage.percent,
                    read_bytes=read_bytes,
                    write_bytes=write_bytes,
                    read_count=read_count,
                    write_count=write_count
                ))
            except Exception as e:
                logger.warning(f"Failed to get disk metrics for {path}: {e}")
        
        return disks
    
    def get_network_metrics(self) -> List[NetworkMetrics]:
        """Get network interface metrics."""
        networks = []
        stats = psutil.net_io_counters(pernic=True)
        
        for interface, counters in stats.items():
            if interface != 'lo':  # Skip loopback
                networks.append(NetworkMetrics(
                    interface=interface,
                    bytes_sent=counters.bytes_sent,
                    bytes_recv=counters.bytes_recv,
                    packets_sent=counters.packets_sent,
                    packets_recv=counters.packets_recv,
                    errors_in=counters.errin,
                    errors_out=counters.errout
                ))
        
        return networks
    
    async def get_snapshot(self) -> SystemSnapshot:
        """Get complete system snapshot."""
        import time
        boot_time = psutil.boot_time()
        
        snapshot = SystemSnapshot(
            timestamp=datetime.now(),
            cpu=self.get_cpu_metrics(),
            memory=self.get_memory_metrics(),
            gpus=self.get_gpu_metrics(),
            disks=self.get_disk_metrics(),
            networks=self.get_network_metrics(),
            process_count=len(psutil.pids()),
            uptime_seconds=time.time() - boot_time
        )
        
        # Check thresholds and generate alerts
        await self._check_alerts(snapshot)
        
        # Store in history
        self._history.append(snapshot)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        return snapshot
    
    async def _check_alerts(self, snapshot: SystemSnapshot):
        """Check resource thresholds and generate alerts."""
        alerts = []
        
        # CPU alert
        if snapshot.cpu.usage_percent > self.thresholds["cpu_percent"]:
            alerts.append(ResourceAlert(
                level=AlertLevel.CRITICAL if snapshot.cpu.usage_percent > 95 else AlertLevel.WARNING,
                resource="cpu",
                message=f"High CPU usage: {snapshot.cpu.usage_percent:.1f}%",
                value=snapshot.cpu.usage_percent,
                threshold=self.thresholds["cpu_percent"],
                timestamp=snapshot.timestamp
            ))
        
        # Memory alert
        if snapshot.memory.usage_percent > self.thresholds["memory_percent"]:
            alerts.append(ResourceAlert(
                level=AlertLevel.CRITICAL if snapshot.memory.usage_percent > 95 else AlertLevel.WARNING,
                resource="memory",
                message=f"High memory usage: {snapshot.memory.usage_percent:.1f}%",
                value=snapshot.memory.usage_percent,
                threshold=self.thresholds["memory_percent"],
                timestamp=snapshot.timestamp
            ))
        
        # GPU alerts
        for gpu in snapshot.gpus:
            if gpu.memory_percent > self.thresholds["gpu_memory_percent"]:
                alerts.append(ResourceAlert(
                    level=AlertLevel.CRITICAL,
                    resource=f"gpu_{gpu.device_id}",
                    message=f"GPU {gpu.device_id} memory critical: {gpu.memory_percent:.1f}%",
                    value=gpu.memory_percent,
                    threshold=self.thresholds["gpu_memory_percent"],
                    timestamp=snapshot.timestamp
                ))
        
        # Disk alerts
        for disk in snapshot.disks:
            if disk.usage_percent > self.thresholds["disk_percent"]:
                alerts.append(ResourceAlert(
                    level=AlertLevel.WARNING,
                    resource=f"disk_{disk.path}",
                    message=f"Disk {disk.path} usage high: {disk.usage_percent:.1f}%",
                    value=disk.usage_percent,
                    threshold=self.thresholds["disk_percent"],
                    timestamp=snapshot.timestamp
                ))
        
        # Trigger callbacks
        for alert in alerts:
            for callback in self.alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(alert)
                    else:
                        callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback failed: {e}")
    
    async def start_continuous_monitoring(self, interval_seconds: float = 5.0):
        """Start continuous background monitoring."""
        self._running = True
        
        async def monitor_loop():
            while self._running:
                try:
                    await self.get_snapshot()
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval_seconds)
        
        self._monitor_task = asyncio.create_task(monitor_loop())
        logger.info(f"Started continuous monitoring (interval: {interval_seconds}s)")
    
    def get_history(self, last_n: Optional[int] = None) -> List[SystemSnapshot]:
        """Get monitoring history."""
        if last_n:
            return self._history[-last_n:]
        return self._history.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get current resource summary."""
        if not self._history:
            return {}
        
        latest = self._history[-1]
        
        return {
            "timestamp": latest.timestamp.isoformat(),
            "cpu_percent": latest.cpu.usage_percent,
            "memory_percent": latest.memory.usage_percent,
            "gpu_memory_percent": max((g.memory_percent for g in latest.gpus), default=0),
            "disk_percent": max((d.usage_percent for d in latest.disks), default=0),
            "process_count": latest.process_count,
            "uptime_hours": latest.uptime_seconds / 3600
        }
