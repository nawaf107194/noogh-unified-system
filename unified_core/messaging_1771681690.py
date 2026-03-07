from abc import ABC, abstractmethod

class MessagingStrategy(ABC):
    @abstractmethod
    def send_message(self, message: str) -> None:
        pass

class EmailMessaging(MessagingStrategy):
    def send_message(self, message: str) -> None:
        # Code to send an email
        print(f"Sending email: {message}")

class SMSMessaging(MessagingStrategy):
    def send_message(self, message: str) -> None:
        # Code to send an SMS
        print(f"Sending SMS: {message}")

class MessagingContext:
    def __init__(self, strategy: MessagingStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: MessagingStrategy) -> None:
        self._strategy = strategy

    def send_message(self, message: str) -> None:
        self._strategy.send_message(message)

# Usage
if __name__ == '__main__':
    context = MessagingContext(EmailMessaging())
    context.send_message("Hello, this is an email.")

    context.set_strategy(SMSMessaging())
    context.send_message("Hello, this is an SMS.")