from typing import Protocol, Dict, Any

class Command(Protocol):
    async def execute(self) -> Dict[str, Any]:
        """Execute the command and return results."""
        ...

class CommandDispatcher:
    def __init__(self):
        self.commands = {}

    async def dispatch(self, command: Command) -> Dict[str, Any]:
        """Dispatch and execute the command."""
        return await command.execute()

    def register(self, command_type: str, command_class: type):
        """Register a new command type."""
        self.commands[command_type] = command_class

# Example usage within InputRouter
class InputRouter:
    def __init__(self):
        self.dispatcher = CommandDispatcher()
        # Register available commands
        self.dispatcher.register("recall", RecallCommand)
        self.dispatcher.register("feedback", FeedbackCommand)

    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        command_type = input_data.get("type")
        command = self.dispatcher.commands.get(command_type)
        if not command:
            raise ValueError(f"Unknown command type: {command_type}")
        return await self.dispatcher.dispatch(command(**input_data))