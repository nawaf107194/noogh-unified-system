import psutil
from typing import Dict, Union
from singleton_decorator import singleton

@singleton
class ResourceGovernor:
    def __init__(self):
        self._cpu_threshold = 80.0  # Percentage
        self._mem_threshold = 80.0  # Percentage
        self._throttle_active = False

    def _get_resource_usage(self) -> Dict[str, Union[float, int]]:
        """Get current system resource metrics"""
        cpu_usage = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        mem_usage = (mem.used / mem.total) * 100
        return {
            'cpu_usage': cpu_usage,
            'mem_usage': mem_usage,
            'timestamp': psutil.boot_time()
        }

    def _is_overloaded(self) -> bool:
        """Check if system is above thresholds"""
        usage = self._get_resource_usage()
        return (
            usage['cpu_usage'] > self._cpu_threshold or
            usage['mem_usage'] > self._mem_threshold
        )

    def get_resource_status(self) -> Dict[str, Union[float, bool]]:
        """Return current resource status"""
        usage = self._get_resource_usage()
        overloaded = self._is_overloaded()
        return {
            **usage,
            'overloaded': overloaded
        }

    def should_throttle(self) -> bool:
        """Determine if brain calls should be throttled"""
        if self._throttle_active:
            return True
        status = self.get_resource_status()
        return status['overloaded']

    def set_throttle(self, enabled: bool) -> None:
        """Enable/disable throttling"""
        self._throttle_active = enabled

    def get_recommendations(self) -> Dict[str, Union[float, int]]:
        """Get recommendations to reduce load"""
        if not self.should_throttle():
            return {'recommendation': 'No action needed'}
        return {
            'recommendation': 'Throttle brain calls',
            'cpu_load': self._cpu_threshold,
            'mem_load': self._mem_threshold
        }

if __name__ == '__main__':
    governor = ResourceGovernor()
    print("Resource Status:")
    print(governor.get_resource_status())
    print("\nRecommendations:")
    print(governor.get_recommendations())