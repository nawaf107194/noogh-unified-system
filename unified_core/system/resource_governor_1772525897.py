import psutil
import logging
from typing import Dict, Any
from unified_core.system.data_router import DataRouter

class ResourceGovernor:
    def __init__(self, data_router: DataRouter):
        self.data_router = data_router
        self.resource_limits = {
            'cpu_percent': 80,
            'gpu_percent': 70,
            'memory_usage': 80
        }
        self.current_load: Dict[str, float] = {}
        self.throttle_active = False

    def get_system_load(self) -> Dict[str, float]:
        """Fetch current system resource utilization."""
        load = {
            'cpu_percent': psutil.cpu_percent(),
            'gpu_percent': self._get_gpu_usage(),
            'memory_usage': psutil.virtual_memory().percent
        }
        return load

    def _get_gpu_usage(self) -> float:
        """Fetch GPU utilization. Requires nvidia-smi."""
        try:
            return psutil.nvidia_smi_get_gpus()[0]['utilization']['gpu']
        except Exception:
            return 0.0

    def check_resource_limits(self) -> bool:
        """Check if any resource utilization exceeds thresholds."""
        load = self.get_system_load()
        self.current_load = load
        
        over_limits = any(
            load[resource] > self.resource_limits[resource]
            for resource in self.resource_limits
        )
        return over_limits

    def apply_throttling(self) -> None:
        """Apply adaptive throttling based on current load."""
        if not self.throttle_active:
            logging.info("ResourceGovernor: Applying throttling measures")
            self.data_router.throttle_model_calls()
            self.throttle_active = True
        else:
            logging.warning("ResourceGovernor: Already throttled, load remains high")

    def release_throttling(self) -> None:
        """Release throttling if resources are under utilization."""
        if self.throttle_active:
            logging.info("ResourceGovernor: Releasing throttling")
            self.data_router.resume_model_calls()
            self.throttle_active = False

    def monitor_and_adjust(self) -> None:
        """Main monitoring loop."""
        over_limits = self.check_resource_limits()
        
        if over_limits:
            self.apply_throttling()
        else:
            self.release_throttling()

if __name__ == '__main__':
    import time
    from unified_core.system.data_router import DataRouter
    
    # Initialize with real data router
    data_router = DataRouter()
    governor = ResourceGovernor(data_router)
    
    while True:
        governor.monitor_and_adjust()
        time.sleep(10)