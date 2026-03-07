from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

class SecureCommand(Command):
    def execute(self):
        # Execution logic for secure command
        print("Executing secure command")

class AsyncCommand(Command):
    async def execute(self):
        # Asynchronous execution logic
        import asyncio
        await asyncio.sleep(1)
        print("Asynchronous command executed")

class CommandExecutor:
    def __init__(self, command: Command):
        self.command = command

    def run_command(self):
        if isinstance(self.command, AsyncCommand):
            asyncio.run(self.command.execute())
        else:
            self.command.execute()

# Example usage
def main():
    secure_cmd = SecureCommand()
    async_cmd = AsyncCommand()

    executor1 = CommandExecutor(secure_cmd)
    executor2 = CommandExecutor(async_cmd)

    executor1.run_command()  # Synchronous execution
    executor2.run_command()  # Asynchronous execution

if __name__ == '__main__':
    main()