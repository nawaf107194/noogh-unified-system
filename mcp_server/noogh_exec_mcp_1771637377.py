# mcp_server/noogh_exec_mcp.py

from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

class ShellCommand(Command):
    def __init__(self, command_str: str):
        self.command_str = command_str

    def execute(self):
        # Execute shell command logic here
        print(f"Executing shell command: {self.command_str}")

class ExecutableCommand(Command):
    def __init__(self, executable_path: str, *args):
        self.executable_path = executable_path
        self.args = args

    def execute(self):
        # Execute external executable logic here
        print(f"Executing executable: {self.executable_path} with arguments: {self.args}")

def run_command(command: Command):
    command.execute()

# Example usage in noogh_mcp.py
if __name__ == '__main__':
    shell_cmd = ShellCommand("ls -la")
    exec_cmd = ExecutableCommand("/usr/bin/python3", "script.py")

    run_command(shell_cmd)
    run_command(exec_cmd)