# unified_core/intent_injector.py

from abc import ABC, abstractmethod

class IntentHandlingStrategy(ABC):
    @abstractmethod
    def handle_intent(self, intent):
        pass

class DefaultIntentHandler(IntentHandlingStrategy):
    def handle_intent(self, intent):
        print(f"Default handling of intent: {intent}")

class PriorityIntentHandler(IntentHandlingStrategy):
    def handle_intent(self, intent):
        print(f"Priority handling of intent: {intent}")

class IntentInjector:
    def __init__(self, strategy: IntentHandlingStrategy = DefaultIntentHandler()):
        self.strategy = strategy

    def set_strategy(self, strategy: IntentHandlingStrategy):
        self.strategy = strategy

    def inject_intent(self, intent):
        self.strategy.handle_intent(intent)

# Example usage in main.py
if __name__ == '__main__':
    injector = IntentInjector()
    injector.inject_intent("User registration")

    # Change strategy dynamically
    injector.set_strategy(PriorityIntentHandler())
    injector.inject_intent("User registration")