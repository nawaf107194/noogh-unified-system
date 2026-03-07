import contextlib
import io
import json
import logging
import math
import multiprocessing
import random
import time

logger = logging.getLogger(__name__)


class CodeExecutor:
    """
    Secure Python Execution Sandbox.
    """

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        logger.info(f"CodeExecutor initialized with timeout={timeout}s")

    def execute(self, code: str) -> str:
            queue = multiprocessing.Queue()
            p = multiprocessing.Process(target=self._safe_exec, args=(code, queue))
            p.start()
            p.join(timeout=self.timeout)

            if p.is_alive():
                p.terminate()
                logger.error("Code execution timed out.")
                return "Error: Execution timed out."

            if queue.empty():
                logger.warning("Queue was empty after process execution.")
                return "No output."

            return queue.get()

    def _safe_exec(self, code: str, queue: multiprocessing.Queue):
        output_capture = io.StringIO()

        # Strict Global Isolation
        # No builtins allowed. Only whitelisted math/time/json libs.
        safe_globals = {
            "__builtins__": {},
            "math": math,
            "time": time,
            "json": json,
            "random": random,
            "print": print,
        }

        try:
            # 1. AST Validation
            import ast
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Ban Imports
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    raise SecurityError("Imports are forbidden.")
                # Ban weird attribute access (basic heuristic, can be bypassed but better than nothing)
                if isinstance(node, ast.Attribute):
                    if node.attr.startswith("__"):
                        raise SecurityError("Double-underscore attributes forbidden.")

            # 2. Execution with Restricted Globals
            with contextlib.redirect_stdout(output_capture), contextlib.redirect_stderr(output_capture):
                exec(code, safe_globals)
            
            # 3. Output Truncation (Anti-DoS)
            output = output_capture.getvalue()
            if len(output) > 2048:
                output = output[:2048] + "... [TRUNCATED]"
            
            queue.put(output)

        except Exception as e:
            queue.put(f"Runtime Error: {str(e)}")

class SecurityError(Exception):
    pass

