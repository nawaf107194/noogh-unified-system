import logging
import shlex
import subprocess

logger = logging.getLogger(__name__)


class ShellExecutor:
    """
    Executes shell commands.
    """

    def __init__(self, allowed_commands: list = None):
        self.allowed_commands = allowed_commands or ["ls", "echo", "pwd", "whoami", "date"]
        logger.info(f"ShellExecutor initialized. Allowed: {self.allowed_commands}")

    def execute(self, command: str) -> str:
            """
            Executes a shell command if allowed.
            """
            cmd_parts = shlex.split(command)
            if not cmd_parts:
                logger.warning("Empty command received.")
                return "Empty command."

            base_cmd = cmd_parts[0]

            if "*" not in self.allowed_commands and base_cmd not in self.allowed_commands:
                logger.warning(f"Command denied: {base_cmd}")
                return f"Error: Command '{base_cmd}' is not allowed."

            try:
                result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=5)
                return result.stdout + result.stderr
            except subprocess.TimeoutExpired as e:
                logger.error(f"Shell execution timed out: {e}")
                return f"Error: Execution timed out."
            except Exception as e:
                logger.error(f"Shell execution failed: {e}")
                return f"Error: {str(e)}"
