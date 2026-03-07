# unified_core/state.py

from abc import ABC, abstractmethod

class StateObserver(ABC):
    @abstractmethod
    def update(self, state: dict) -> None:
        pass

class StateManager:
    def __init__(self):
        self.observers = []

    def add_observer(self, observer: StateObserver) -> None:
        self.observers.append(observer)

    def remove_observer(self, observer: StateObserver) -> None:
        self.observers.remove(observer)

    def notify_observers(self, state: dict) -> None:
        for observer in self.observers:
            observer.update(state)

    def set_state(self, state: dict) -> None:
        # Update the state logic here
        self.notify_observers(state)