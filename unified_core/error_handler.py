# unified_core/messaging.py

from .error_handler import handle_errors

class MessageHandler:
    
    @handle_errors
    async def send_message(self, message: str) -> None:
        # Simulated message sending logic
        print(f"Sending message: {message}")
        
    @handle_errors
    async def receive_message(self) -> str:
        # Simulated message receiving logic
        return "Received message"