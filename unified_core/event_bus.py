from typing import Dict, List, Type, Callable

class EventSubscriber:
    def __init__(self, event_type: Type, handler: Callable):
        self.event_type = event_type
        self.handler = handler

class EventBus:
    def __init__(self):
        self.subscribers: Dict[Type, List[EventSubscriber]] = {}

    def subscribe(self, event_type: Type, handler: Callable) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(EventSubscriber(event_type, handler))

    async def publish(self, event) -> None:
        event_type = type(event)
        if event_type in self.subscribers:
            for subscriber in self.subscribers[event_type]:
                await subscriber.handler(event)

    @staticmethod
    def get_instance() -> 'EventBus':
        if not hasattr(EventBus, '_instance'):
            EventBus._instance = EventBus()
        return EventBus._instance