from unified_core.system.resource_governor import ResourceGovernor
from unified_core.system.neural_bridge import NeuralBridge
from unified_core.system.data_router import DataRouter
import logging
import time

class AutonomousResourceManager:
    def __init__(self):
        self.resource_governor = ResourceGovernor()
        self.neural_bridge = NeuralBridge()
        self.data_router = DataRouter()
        self.last_check = 0
        self.check_interval = 5  # seconds between checks

    def _get_resource_usage(self):
        """Get current system resource usage metrics"""
        return {
            'cpu_percent': self.resource_governor.get_cpu_usage(),
            'gpu_usage': self.resource_governor.get_gpu_usage(),
            'memory_usage': self.resource_governor.get_memory_usage()
        }

    def _adjust_component_priorities(self, usage_metrics):
        """Adjust component priorities based on current resource usage"""
        # Get current component loads
        component_loads = {
            'neural_bridge': self.neural_bridge.get_current_load(),
            'data_router': self.data_router.get_current_load(),
            # Add other components as needed
        }

        # Calculate total system load
        total_load = sum(component_loads.values())
        
        # If system is under heavy load, prioritize critical components
        if total_load > 80:
            self.resource_governor.set_priority('neural_bridge', 90)
            self.resource_governor.set_priority('data_router', 80)
        else:
            # Return to normal priority levels
            self.resource_governor.set_priority('neural_bridge', 70)
            self.resource_governor.set_priority('data_router', 60)

    def monitor_and_adjust(self):
        """Main monitoring loop"""
        while True:
            current_time = time.time()
            
            if current_time - self.last_check > self.check_interval:
                try:
                    usage_metrics = self._get_resource_usage()
                    self._adjust_component_priorities(usage_metrics)
                    self.last_check = current_time
                except Exception as e:
                    logging.error(f"Resource management error: {str(e)}")
            
            time.sleep(1)

if __name__ == '__main__':
    manager = AutonomousResourceManager()
    manager.monitor_and_adjust()