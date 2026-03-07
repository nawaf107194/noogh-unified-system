"""
SystemMonitor - Monitors system resources and health
"""

import logging
import platform
from typing import Any, Dict

import psutil

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitors Linux system resources"""

    def __init__(self):
        """Initialize SystemMonitor"""
        logger.info("SystemMonitor initialized")

    def get_system_info(self) -> Dict[str, Any]:
        """Get complete system information"""
        return {
            "os": self.get_os_info(),
            "cpu": self.get_cpu_info(),
            "memory": self.get_memory_info(),
            "disk": self.get_disk_info(),
            "network": self.get_network_info(),
            "gpu": self.get_gpu_info(),
        }

    def get_os_info(self) -> Dict[str, str]:
        """Get OS information"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information"""
        return {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "max_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else 0,
            "current_frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "per_cpu_usage": psutil.cpu_percent(interval=1, percpu=True),
        }

    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory information"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent,
            "swap_total": swap.total,
            "swap_used": swap.used,
            "swap_percent": swap.percent,
        }

    def get_disk_info(self) -> Dict[str, Any]:
        """Get disk information"""
        partitions = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append(
                    {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent,
                    }
                )
            except PermissionError:
                continue

        return {"partitions": partitions}

    def get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        net_io = psutil.net_io_counters()

        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
        }

    def get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information"""
        try:
            import torch

            if torch.cuda.is_available():
                return {
                    "available": True,
                    "name": torch.cuda.get_device_name(0),
                    "memory_total": torch.cuda.get_device_properties(0).total_memory,
                    "memory_allocated": torch.cuda.memory_allocated(0),
                    "memory_reserved": torch.cuda.memory_reserved(0),
                }
        except Exception:
            pass

        return {"available": False}

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health"""
        cpu = self.get_cpu_info()
        mem = self.get_memory_info()
        disk = self.get_disk_info()

        # Determine health
        health = "healthy"
        warnings = []

        if cpu["cpu_usage_percent"] > 90:
            health = "warning"
            warnings.append("High CPU usage")

        if mem["percent"] > 90:
            health = "critical"
            warnings.append("High memory usage")

        for partition in disk["partitions"]:
            if partition["percent"] > 90:
                health = "warning"
                warnings.append(f"Disk {partition['mountpoint']} almost full")

        return {
            "status": health,
            "warnings": warnings,
            "cpu_usage": cpu["cpu_usage_percent"],
            "memory_usage": mem["percent"],
        }

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Unified dashboard telemetry"""
        return {
            "system": self.get_health_status(),
            "resources": {"cpu": self.get_cpu_info(), "memory": self.get_memory_info(), "gpu": self.get_gpu_info()},
        }

    def get_process_manager(self):
        return ProcessManager()


class ProcessManager:
    """Manages system processes"""

    def __init__(self):
        logger.info("ProcessManager initialized")

    def list_processes(self, limit: int = 10) -> list:
        """List running processes"""
        processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by CPU usage
        processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
        return processes[:limit]

    def get_process_info(self, pid: int) -> Dict[str, Any]:
        """Get detailed process information"""
        try:
            proc = psutil.Process(pid)
            return {
                "pid": proc.pid,
                "name": proc.name(),
                "status": proc.status(),
                "cpu_percent": proc.cpu_percent(),
                "memory_percent": proc.memory_percent(),
                "num_threads": proc.num_threads(),
            }
        except psutil.NoSuchProcess:
            return {"error": "Process not found"}


class FileManager:
    """Manages files and directories"""

    def __init__(self):
        logger.info("FileManager initialized")

    def get_directory_size(self, path: str) -> int:
        """Get total size of directory"""
        import os

        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self.get_directory_size(entry.path)
        except PermissionError:
            pass
        return total


class CommandExecutor:
    """Executes system commands safely"""

    def __init__(self):
        self.command_history = []
        logger.info("CommandExecutor initialized")

    def execute(self, command: str, safe_mode: bool = True) -> Dict[str, Any]:
        """Execute a system command"""
        import subprocess

        # Safety check
        if safe_mode:
            dangerous_commands = ["rm -rf", "mkfs", "dd", ":(){:|:&};:"]
            if any(cmd in command for cmd in dangerous_commands):
                return {"error": "Dangerous command blocked", "command": command}

        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)

            self.command_history.append({"command": command, "success": result.returncode == 0})

            return {
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timeout", "command": command}
        except Exception as e:
            return {"error": str(e), "command": command}


if __name__ == "__main__":
    # Test system monitoring
    monitor = SystemMonitor()

    print("🖥️  System Information:")
    print("-" * 50)

    os_info = monitor.get_os_info()
    print(f"OS: {os_info['system']} {os_info['release']}")

    cpu_info = monitor.get_cpu_info()
    print(f"CPU: {cpu_info['total_cores']} cores @ {cpu_info['cpu_usage_percent']}%")

    mem_info = monitor.get_memory_info()
    print(f"Memory: {mem_info['percent']}% used")

    health = monitor.get_health_status()
    print(f"\nHealth: {health['status']}")
    if health["warnings"]:
        for warning in health["warnings"]:
            print(f"  ⚠️  {warning}")
