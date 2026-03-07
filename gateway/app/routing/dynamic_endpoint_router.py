import random
from typing import Dict, List, Tuple

class DynamicEndpointRouter:
    def __init__(self, endpoints: List[Tuple[str, int]]):
        """
        Initialize the router with a list of endpoints and their current loads.
        
        :param endpoints: List of tuples where each tuple contains an endpoint name and its current load.
        """
        self.endpoints = endpoints
        self.endpoint_map = {name: load for name, load in endpoints}

    def update_load(self, endpoint_name: str, new_load: int) -> None:
        """
        Update the load of a specific endpoint.
        
        :param endpoint_name: Name of the endpoint to update.
        :param new_load: New load value for the endpoint.
        """
        if endpoint_name in self.endpoint_map:
            self.endpoint_map[endpoint_name] = new_load
        else:
            raise ValueError(f"Endpoint {endpoint_name} not found.")

    def get_least_loaded_endpoint(self) -> str:
        """
        Return the name of the least loaded endpoint.
        """
        return min(self.endpoint_map, key=self.endpoint_map.get)

    def route_request(self) -> str:
        """
        Route a request to the least loaded endpoint.
        """
        least_loaded = self.get_least_loaded_endpoint()
        # Simulate increasing the load after routing a request
        self.update_load(least_loaded, self.endpoint_map[least_loaded] + 1)
        return least_loaded

# Example usage
endpoints = [("chat", 10), ("tasks", 5), ("memory", 20)]
router = DynamicEndpointRouter(endpoints)
print(router.route_request())  # Routes to the least loaded endpoint and updates its load