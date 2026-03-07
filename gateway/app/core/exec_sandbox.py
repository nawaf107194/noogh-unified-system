import contextlib
import io
import json
import math
import multiprocessing
import random
import re
import resource
import time

from gateway.app.core.config import get_settings
from gateway.app.core.logging import get_logger

settings = get_settings()
logger = get_logger("exec_sandbox")


class ExecSandbox:
    def extract_exec_blocks(self, text: str) -> list[str]:
        """
        Extract code blocks marked with ```python ... ``` or just ``` ... ```
        Handles both with and without newlines after opening backticks.
        """
        # Updated pattern: optional newline after opening backticks
        pattern = r"```(?:python)?\s*(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return [m.strip() for m in matches if m.strip()]

    def run_exec(self, code: str) -> str:
        if not settings.ALLOW_EXEC:
            return "Execution disabled by configuration."

        # Limit code length to prevent memory exhaustion
        MAX_CODE_LENGTH = 10000  # 10KB
        if len(code) > MAX_CODE_LENGTH:
            return f"Error: Code too long ({len(code)} chars). Maximum allowed: {MAX_CODE_LENGTH}"

        logger.info("Preparing to execute code block...")

        # Create a queue to capture output with size limit
        # Use spawn context to avoid deadlocks in threaded environments (like pytest)
        ctx = multiprocessing.get_context("spawn")
        queue = ctx.Queue(maxsize=1024)

        # Process wrapper
        p = ctx.Process(target=self._safe_exec, args=(code, queue))
        p.start()
        p.join(timeout=settings.EXEC_TIMEOUT)

        if p.is_alive():
            # Attempt graceful termination
            p.terminate()
            # give a short grace period
            p.join(timeout=1)
            if p.is_alive():
                try:
                    p.kill()
                except Exception:
                    pass
            logger.error("Execution timed out and killed.")
            return f"Error: Execution timed out after {settings.EXEC_TIMEOUT}s"

        if not queue.empty():
            result = queue.get()
            return result

        return "No output produced."

    def _safe_exec(self, code: str, queue: multiprocessing.Queue):
        # Capture stdout/stderr
        output_capture = io.StringIO()

        # Restricted globals
        safe_globals = {
            "math": math,
            "time": time,
            "json": json,
            "re": re,
            "random": random,
            "print": print,
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "int": int,
                "float": float,
                "str": str,
                "list": list,
                "dict": dict,
                "set": set,
                "bool": bool,
                "sum": sum,
                "min": min,
                "max": max,
                "sorted": sorted,
                "abs": abs,
                "round": round,
            },
        }

        try:
            # Apply hard OS resource limits in child process (RLIMITs)
            try:
                # Address space: 256 MB
                resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
                # CPU seconds: 5s
                resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
                # Max processes: 512 (Threads count as processes on Linux, needed for Queue)
                resource.setrlimit(resource.RLIMIT_NPROC, (512, 512))
                # Max open files: 1024 (Python imports need files)
                resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024))
            except Exception:
                # If RLIMITs not available, continue but log
                logger.warning("Could not apply resource limits in sandbox child process.")
            from gateway.app.core.ast_validator import validate_python

            vr = validate_python(code)
            if not vr.ok:
                queue.put("AST_VALIDATION_FAILED:\n" + "\n".join(vr.reasons))
                return

            with contextlib.redirect_stdout(output_capture), contextlib.redirect_stderr(output_capture):
                exec(code, safe_globals)

            queue.put(output_capture.getvalue())
        except Exception as e:
            queue.put(f"Runtime Error: {str(e)}")
