from typing import List
from unified_core.system.gateway import GatewayClient

class MultiAgent:
    def __init__(self, gateway_client: GatewayClient):
        self.gateway_client = gateway_client

    def spawn_sub_agents(self, task_list: List[str]):
        """Spawn sub-agents for parallel execution of tasks."""
        for task in task_list:
            self.gateway_client.spawn_task(task)

    def manage_agents(self):
        """Monitor and manage the spawned agents to ensure they complete their tasks efficiently."""
        while True:
            active_tasks = self.gateway_client.get_active_tasks()
            if not active_tasks:
                break
            # Add logic to handle agent failures, retries, etc.
            time.sleep(1)  # Simulate monitoring interval

    def retrieve_results(self):
        """Retrieve the results from completed tasks."""
        results = []
        while True:
            completed_tasks = self.gateway_client.get_completed_tasks()
            if not completed_tasks:
                break
            for task in completed_tasks:
                results.append(task.result)
            time.sleep(1)  # Simulate retrieval interval
        return results

if __name__ == '__main__':
    from unified_core.system.gateway import GatewayClient

    gateway_client = GatewayClient()
    multi_agent = MultiAgent(gateway_client)

    tasks = [
        "task_1",
        "task_2",
        "task_3"
    ]

    multi_agent.spawn_sub_agents(tasks)
    multi_agent.manage_agents()
    results = multi_agent.retrieve_results()

    print("Completed Tasks Results:", results)