import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HealthCheck:
    """
    A utility class to perform health checks on different components of the system.
    """

    def __init__(self):
        self.statuses: Dict[str, Dict[str, Any]] = {}

    def add_status(self, component_name: str, status: Dict[str, Any]):
        """
        Adds the health status of a component to the internal tracker.
        
        :param component_name: The name of the component.
        :param status: A dictionary containing the health status information.
        """
        self.statuses[component_name] = status

    def get_overall_status(self) -> bool:
        """
        Returns the overall health status of the system.
        
        :return: True if all components report healthy status, False otherwise.
        """
        return all(status.get('healthy', False) for status in self.statuses.values())

    def report(self) -> None:
        """
        Logs the health status of each component and the overall status of the system.
        """
        logger.info("Health Check Report:")
        for component, status in self.statuses.items():
            logger.info(f"Component: {component}, Status: {status}")
        overall_status = self.get_overall_status()
        logger.info(f"Overall System Health: {'Healthy' if overall_status else 'Unhealthy'}")

# Example usage within a component
def check_neural_engine_health() -> Dict[str, Any]:
    # Simulated health check logic
    is_healthy = True  # Replace with actual health check logic
    return {
        'healthy': is_healthy,
        'details': 'Neural Engine is operational.'
    }

# Main health check instance
health_checker = HealthCheck()

# Add health statuses from different components
neural_engine_status = check_neural_engine_health()
health_checker.add_status('Neural Engine', neural_engine_status)

# Other components can similarly report their health status

# Report the overall health status
health_checker.report()