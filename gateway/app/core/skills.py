import os
from typing import Any, Dict



class AgentSkills:
    """High-Level Safe Skills."""

    def __init__(self, safe_root: str):
        self.safe_root = safe_root

    def _ensure_safe_path(self, path: str) -> str:
        """Ensure path is within safe_root."""
        if not path:
            path = "."
        safe_root_abs = os.path.abspath(self.safe_root)
        if os.path.isabs(path):
            candidate = os.path.abspath(path)
        else:
            candidate = os.path.abspath(os.path.join(safe_root_abs, path))
        if not (candidate == safe_root_abs or candidate.startswith(safe_root_abs + os.sep)):
            raise ValueError(f"Path '{path}' is outside of SAFE_ROOT")
        return candidate

    def repo_overview(self, workspace_dir: str) -> Dict[str, Any]:
        summary = [f"Repo Overview for: {workspace_dir}"]
        try:
            for root, dirs, files in os.walk(workspace_dir):
                level = root.replace(workspace_dir, "").count(os.sep)
                if level > 2:
                    continue
                indent = " " * 4 * level
                summary.append(f"{indent}{os.path.basename(root)}/")
                subindent = " " * 4 * (level + 1)
                for f in files[:10]:
                    summary.append(f"{subindent}{f}")
                if len(files) > 10:
                    summary.append(f"{subindent}... ({len(files)-10} more)")
            return {"success": True, "output": "\n".join(summary)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def find_entrypoints(self, workspace_dir: str) -> Dict[str, Any]:
        candidates = ["main.py", "app.py", "wsgi.py", "server.py", "manage.py"]
        found = []
        try:
            for root, _, files in os.walk(workspace_dir):
                for f in files:
                    if f in candidates:
                        found.append(os.path.join(root, f))
            return {"success": True, "output": "\n".join(found) if found else "None"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_file(self, path: str) -> Dict[str, Any]:
        try:
            abs_path = self._ensure_safe_path(path)
            if not os.path.exists(abs_path):
                return {"success": False, "error": "Not found", "size_bytes": 0}
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return {"success": True, "output": content, "size_bytes": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        try:
            abs_path = self._ensure_safe_path(path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "output": f"Wrote {len(content)} bytes", "size_bytes": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_files(self, path: str = ".") -> Dict[str, Any]:
        try:
            abs_path = self._ensure_safe_path(path)
            items = os.listdir(abs_path)
            return {"success": True, "output": "\n".join(items)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_python_code(self, code: str) -> Dict[str, Any]:
        import sys
        from io import StringIO

        old_stdout = sys.stdout
        redirected_output = StringIO()
        sys.stdout = redirected_output
        try:
            exec(code, {"__builtins__": __builtins__})
            return {"success": True, "output": redirected_output.getvalue() or "(No output)"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            sys.stdout = old_stdout

    def search_code(self, workspace_dir: str, pattern: str) -> Dict[str, Any]:
        import re

        matches = []
        try:
            for root, _, files in os.walk(workspace_dir):
                for file in files:
                    if file.endswith((".py", ".js", ".ts")):
                        filepath = os.path.join(root, file)
                        with open(filepath, "r", errors="ignore") as f:
                            if re.search(pattern, f.read(), re.IGNORECASE):
                                matches.append(filepath)
                if len(matches) >= 20:
                    break
            return {"success": True, "output": "\n".join(matches)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_tests(self, test_path: str = ".") -> Dict[str, Any]:
        """
        Run tests - BLOCKED for security.
        
        SECURITY: Direct subprocess execution bypasses ProcessActuator.
        Use unified_core/core/actuators.py:ProcessActuator.spawn() instead.
        """
        if not isinstance(test_path, str):
            logger.error("Input validation failed: test_path is not a string.")
            raise TypeError("test_path must be a string")
        
        if not test_path:
            logger.error("Input validation failed: test_path cannot be an empty string.")
            raise ValueError("test_path cannot be an empty string")

        # Simulate input validation and logging for robustness
        logger.info(f"Received request to run tests at path: {test_path}")
        
        result = {
            "success": False, 
            "error": "SECURITY_BLOCKED: run_tests() disabled. Use ProcessActuator.spawn() for subprocess execution.",
            "blocked_reason": "Direct subprocess bypasses ALLOWED_COMMANDS allowlist"
        }
        
        logger.warning(result["error"])
        return result

    def git_status(self) -> Dict[str, Any]:
        """Get current git status - BLOCKED for security."""
        return {
            "success": False,
            "error": "SECURITY_BLOCKED: git_status() disabled. Use ProcessActuator.spawn() with git in ALLOWED_COMMANDS."
        }

    def git_diff(self) -> Dict[str, Any]:
        """Get git diff - BLOCKED for security."""
        return {
            "success": False,
            "error": "SECURITY_BLOCKED: git_diff() disabled. Use ProcessActuator.spawn() with git in ALLOWED_COMMANDS."
        }

    def create_plan(self, task: str) -> Dict[str, Any]:
        """Create a plan for a task."""
        # Simple placeholder for now, returning success to satisfy tool execution
        return {"success": True, "plan": f"Plan for: {task}"}


def get_skills_instance(data_dir: str) -> AgentSkills:
    """Factory for AgentSkills."""
    if not data_dir:
        data_dir = "."
    return AgentSkills(safe_root=data_dir)
