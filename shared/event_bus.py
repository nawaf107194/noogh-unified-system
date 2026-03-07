import queue
import threading

class EventBus:
    def __init__(self):
        self._event_queue = queue.Queue()
        self._listeners = {}
        self._thread = threading.Thread(target=self._run_listener, daemon=True)
        self._thread.start()

    def register_listener(self, event_type, callback):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def unregister_listener(self, event_type, callback):
        if event_type in self._listeners:
            self._listeners[event_type].remove(callback)
            if not self._listeners[event_type]:
                del self._listeners[event_type]

    def publish_event(self, event_type, data):
        self._event_queue.put((event_type, data))

    def _run_listener(self):
        while True:
            event_type, data = self._event_queue.get()
            if event_type in self._listeners:
                for callback in self._listeners[event_type]:
                    callback(data)
            self._event_queue.task_done()

# Example usage
def on_data_received(data):
    print(f"Received data: {data}")

def main():
    event_bus = EventBus()
    event_bus.register_listener('DATA_RECEIVED', on_data_received)
    event_bus.publish_event('DATA_RECEIVED', {'key': 'value'})

if __name__ == "__main__":
    main()