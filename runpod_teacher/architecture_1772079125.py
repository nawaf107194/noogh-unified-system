# runpod_teacher/consolidated_utils.py

class ConnectionStrategy:
    def connect(self):
        raise NotImplementedError("This method should be overridden by subclasses")

class DataRouterConnection(ConnectionStrategy):
    def connect(self):
        # Logic to connect to DataRouter
        print("Connecting to DataRouter")
        return "DataRouterConnection"

class SomeOtherServiceConnection(ConnectionStrategy):
    def connect(self):
        # Logic to connect to SomeOtherService
        print("Connecting to SomeOtherService")
        return "SomeOtherServiceConnection"

class TrajectoryRecorder:
    def __init__(self, strategy: ConnectionStrategy):
        self.strategy = strategy

    def record_trajectory(self):
        connection = self.strategy.connect()
        print(f"Recording trajectory using {connection}")

# Example usage
if __name__ == '__main__':
    data_router_strategy = DataRouterConnection()
    recorder = TrajectoryRecorder(data_router_strategy)
    recorder.record_trajectory()

    some_other_service_strategy = SomeOtherServiceConnection()
    another_recorder = TrajectoryRecorder(some_other_service_strategy)
    another_recorder.record_trajectory()