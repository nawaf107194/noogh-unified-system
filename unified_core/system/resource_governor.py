# unified_core/system/resource_governor.py

import time
from threading import Lock
import psutil

class ResourceGovernor:
    def __init__(self, max_cpu_usage=0.85, max_gpu_memory=0.75):
        self.max_cpu_usage = max_cpu_usage
        self.max_gpu_memory = max_gpu_memory
        self.cpu_lock = Lock()
        self.gpu_lock = Lock()

    def check_and_throttle(self):
        cpu_usage = psutil.cpu_percent(interval=1)
        gpu_memory = self._get_gpu_memory_usage()

        if cpu_usage > self.max_cpu_usage:
            with self.cpu_lock:
                print(f"CPU usage exceeded {self.max_cpu_usage * 100}%. Throttling...")
                time.sleep(2)  # Simulate throttling by pausing for a bit

        if gpu_memory > self.max_gpu_memory:
            with self.gpu_lock:
                print(f"GPU memory usage exceeded {self.max_gpu_memory * 100}%. Throttling...")
                time.sleep(2)  # Simulate throttling by pausing for a bit

    def _get_gpu_memory_usage(self):
        # This is a placeholder. In a real scenario, you would use a library like GPUtil to fetch GPU memory usage.
        return 0.65  # Example value

if __name__ == '__main__':
    governor = ResourceGovernor()
    
    while True:
        governor.check_and_throttle()
        time.sleep(1)