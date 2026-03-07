import logging
import time
import tempfile
import os
import subprocess
from typing import Dict, Any

logger = logging.getLogger("sandbox.docker")

class LocalDockerSandbox:
    """
    Executes Python code in a secure ephemeral Docker container.
    """
    def __init__(self, image: str = "python:3.12-slim", timeout: int = 10):
        self.image = image
        self.timeout = timeout
        
    def execute_code(self, code: str, language: str = "python", timeout: int = None) -> Dict[str, Any]:
        if language != "python":
            return {"success": False, "error": "Only python supported locally", "output": ""}
            
        final_timeout = timeout or self.timeout
        start_time = time.time()
        
        try:
            # 1. Write code to temp file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
                tmp.write(code)
                tmp_path = tmp.name
                
            # 2. Prepare Docker Command
            # Mount the script read-only
            filename = os.path.basename(tmp_path)
            local_dir = os.path.dirname(tmp_path)
            
            # Secure execution: readonly, net-none, memory limit, cpu limit
            cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "--memory", "128m",
                "--cpus", "0.5",
                "-v", f"{tmp_path}:/app/{filename}:ro",
                "-w", "/app",
                self.image,
                "python", filename
            ]
            
            # 3. Execute
            logger.info(f"Running sandbox: {' '.join(cmd)}")
            proc = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=final_timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            success = proc.returncode == 0
            output = proc.stdout
            if proc.stderr:
                output += f"\nSTDERR: {proc.stderr}"
                
            return {
                "success": success,
                "output": output.strip(),
                "error": proc.stderr.strip() if not success else None,
                "exit_code": proc.returncode,
                "duration_ms": duration
            }
            
        except subprocess.TimeoutExpired:
             return {
                "success": False,
                "error": f"Execution Timed Out (> {final_timeout}s)",
                "output": "",
                "exit_code": -1,
                "duration_ms": (time.time() - start_time) * 1000
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Sandbox Error: {str(e)}",
                "output": "",
                "exit_code": -1,
                "duration_ms": (time.time() - start_time) * 1000
            }
        finally:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)

# Singleton
_sandbox = None
def get_local_sandbox():
    global _sandbox
    if _sandbox is None:
        _sandbox = LocalDockerSandbox()
    return _sandbox
