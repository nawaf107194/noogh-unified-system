import abc
import docker
import tarfile
import io
import time
import os
import uuid
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("sandbox_impl")

class SandboxService(abc.ABC):
    """Abstract interface for code execution sandboxes."""
    @abc.abstractmethod
    def execute_code(self, code: str, language: str = "python", timeout: int = 10) -> Dict[str, Any]:
        pass

class DockerSandboxService(SandboxService):
    """
    Executes code in ephemeral Docker containers.
    MOVED FROM GATEWAY for Isolation.
    """
    def __init__(self, image: str = "python:3.12-slim", cpu_quota: int = 50000, mem_limit: str = "128m"):
        self.image = image
        self.client = docker.from_env()
        self.cpu_quota = cpu_quota
        self.mem_limit = mem_limit
        self.workdir = "/tmp"
        
    def execute_code(self, code: str, language: str = "python", timeout: int = 10) -> Dict[str, Any]:
        container = None
        start_time = time.time()
        
        try:
            container = self.client.containers.run(
                self.image,
                command="tail -f /dev/null", 
                detach=True,
                network_mode="none", 
                mem_limit=self.mem_limit,
                cpu_quota=self.cpu_quota,
                pids_limit=20, 
                ulimits=[
                    docker.types.Ulimit(name='nproc', soft=50, hard=50),
                    docker.types.Ulimit(name='nofile', soft=1024, hard=1024)
                ],
                working_dir=self.workdir,
                read_only=True, 
                tmpfs={'/tmp': 'rw,size=64m,noexec'}, 
                cap_drop=["ALL"], 
                security_opt=["no-new-privileges"], 
                user="1000:1000" 
            )
        except docker.errors.APIError as e:
            if "linux spec user" in str(e).lower() or "unable to find user" in str(e).lower():
                logger.critical(f"Security Panic: Requested sandbox user 1000:1000 not found or invalid in image {self.image}. Refusing to fall back to root.")
                raise RuntimeError("Sandbox Security Failure: Invalid User Configuration") from e
            raise e
            
            self._copy_to_container(container, "script.py", code)
            
            exec_start = time.time()
            cmd_str = f"ls -la {self.workdir} && timeout {timeout}s python script.py"
            
            exit_code, output_bytes = container.exec_run(
                cmd=["/bin/sh", "-c", cmd_str],
                workdir=self.workdir,
                user="1000:1000",
                demux=True
            )
            
            duration = (time.time() - exec_start) * 1000
            stdout = output_bytes[0].decode("utf-8", errors="replace") if output_bytes[0] else ""
            stderr = output_bytes[1].decode("utf-8", errors="replace") if output_bytes[1] else ""
            
            if "script.py" not in stdout and exit_code != 0:
                 logger.error(f"Sandbox file missing. LS output: {stdout}")
            
            if exit_code == 124: # Timeout exit code
                return {
                    "success": False,
                    "output": stdout,
                    "error": f"Execution timed out after {timeout}s",
                    "exit_code": exit_code,
                    "duration_ms": duration
                }
            
            success = (exit_code == 0)
            
            return {
                "success": success,
                "output": stdout if success else stdout, 
                "error": stderr if not success else None,
                "exit_code": exit_code,
                "duration_ms": duration
            }

        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "exit_code": -1,
                "duration_ms": (time.time() - start_time) * 1000
            }
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    def _copy_to_container(self, container, filename: str, content: str):
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            data = content.encode('utf-8')
            tar_info = tarfile.TarInfo(name=filename)
            tar_info.size = len(data)
            tar_info.mtime = time.time()
            tar.addfile(tar_info, io.BytesIO(data))
        
        tar_stream.seek(0)
        container.put_archive(path=self.workdir, data=tar_stream)
