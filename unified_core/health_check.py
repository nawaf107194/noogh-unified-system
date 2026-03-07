import time
from typing import Dict

class HealthCheckService:
    def __init__(self):
        self.metrics = {
            'neural_engine': {'status': 'unknown', 'last_update': 0},
            'gateway_api': {'status': 'unknown', 'last_update': 0},
            'agent_daemon': {'status': 'unknown', 'last_update': 0},
            # Add other components as needed
        }

    def update_metric(self, component: str, status: str):
        if component in self.metrics:
            self.metrics[component]['status'] = status
            self.metrics[component]['last_update'] = time.time()
        else:
            raise ValueError(f"Component '{component}' not found.")

    def get_health_status(self) -> Dict[str, Dict]:
        return self.metrics

    def register_component(self, component: str):
        if component not in self.metrics:
            self.metrics[component] = {'status': 'unknown', 'last_update': 0}

# Example usage
if __name__ == "__main__":
    health_checker = HealthCheckService()
    health_checker.register_component('memory_storage')
    
    health_checker.update_metric('neural_engine', 'healthy')
    health_checker.update_metric('gateway_api', 'degraded')
    health_checker.update_metric('agent_daemon', 'healthy')
    
    print(health_checker.get_health_status())