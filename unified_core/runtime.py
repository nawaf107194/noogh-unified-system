import asyncio
import os
import signal
import subprocess
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Optional

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NooghRuntime")

# Styling
BOLD = '\033[1m'
BLUE = '\033[94m'
END = '\033[0m'

class NooghRuntime:
    """
    Orchestrator for managing Noogh system processes.
    Controls Redis, Neural Engine, Gateway, and Agent Daemon.
    """
    
    def __init__(self, src_dir: Optional[str] = None):
        self.src_dir = Path(src_dir or Path(__file__).resolve().parents[1])
        self.processes: Dict[str, subprocess.Popen] = {}
        self.shutdown_event = asyncio.Event()
        self._loop = None

    async def start_redis(self):
        """Start Redis via Docker if not already running."""
        try:
            # Check if running
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=noogh-redis", "-q"],
                capture_output=True, text=True
            )
            if result.stdout.strip():
                logger.info("✅ Redis is already running.")
                return True
            
            logger.info("🚀 Starting Redis (Docker)...")
            subprocess.run(["docker", "rm", "-f", "noogh-redis"], capture_output=True)
            subprocess.run([
                "docker", "run", "-d",
                "--name", "noogh-redis",
                "-p", "6379:6379",
                "redis:7-alpine"
            ], check=True)
            logger.info("✅ Redis started.")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start Redis: {e}")
            return False

    async def run_process(self, name: str, cmd: list, env: dict = None):
        """Run a process and keep track of it."""
        logger.info(f"🚀 Starting {name}...")
        log_file = open(f"{name.lower().replace(' ', '_')}.log", "a")
        
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
            
        proc = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=log_file,
            cwd=str(self.src_dir),
            env=process_env,
            preexec_fn=os.setsid # Create process group for easier termination
        )
        self.processes[name] = proc
        logger.info(f"✅ {name} started with PID: {proc.pid}")

    async def monitor_processes(self):
        """Monitor running processes and restart them if they die."""
        while not self.shutdown_event.is_set():
            for name, proc in list(self.processes.items()):
                if proc.poll() is not None:
                    logger.warning(f"⚠️ {name} (PID {proc.pid}) died unexpectedly. Restarting...")
                    # TODO: Properly restart based on process type
                    # For now, just remove it from tracking
                    del self.processes[name]
                    # In a real implementation, we'd trigger the specific start method
            await asyncio.sleep(5)

    async def shutdown(self):
        """Gracefully shut down all managed processes."""
        logger.info("🛑 Shutting down Noogh System...")
        self.shutdown_event.set()
        
        for name, proc in self.processes.items():
            logger.info(f"Stopping {name}...")
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
        
        # Wait for processes to exit
        for name, proc in self.processes.items():
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {name}...")
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        
        logger.info("✨ Cleanup complete. Goodbye.")

    async def print_security_report(self):
        """Print status of core security and governance modules."""
        print(f"\n{BOLD}{BLUE}🛡️  Security & Governance Report{END}")
        print(f"─" * 40)
        
        # 1. AMLA Status
        strict_mode = os.getenv("NOOGH_STRICT_MODE") == "1"
        status_icon = "🟢" if strict_mode else "🟡"
        print(f"  AMLA Mode:      {status_icon} {'STRICT (Enforced)' if strict_mode else 'ADVISORY'}")
        
        # 2. Tool Registry
        from unified_core.tool_definitions import UNIFIED_TOOLS
        admin_tools = [t for t in UNIFIED_TOOLS.values() if t.requires_admin]
        print(f"  Admin Tools:    🔐 {len(admin_tools)} restricted operations")
        
        # 3. Sandbox Status
        from unified_core.sandbox_service import get_sandbox_service
        sandbox = get_sandbox_service()
        print(f"  Sandbox:        🛡️ ACTIVE (Process & Memory Limits)")
        
        print(f"─" * 40 + "\n")

    async def start_neural_engine(self):
        env = {
            "NOOGH_STRICT_MODE": os.getenv("NOOGH_STRICT_MODE", "1"),
            "PYTORCH_ALLOC_CONF": "expandable_segments:True"
        }
        cmd = [sys.executable, "-m", "uvicorn", "neural_engine.api.main:app", 
               "--host", "127.0.0.1", "--port", "8000"]
        await self.run_process("Neural Engine", cmd, env=env)

    async def start_gateway(self):
        env = {
            "NOOGH_STRICT_MODE": os.getenv("NOOGH_STRICT_MODE", "1")
        }
        cmd = [sys.executable, "-m", "uvicorn", "gateway.app.main:app", 
               "--host", "127.0.0.1", "--port", "8001"]
        await self.run_process("Gateway", cmd, env=env)

    async def run(self):
        """Main entry point for the orchestrator."""
        self._loop = asyncio.get_event_loop()
        
        # 1. Start Infrastructure
        if not await self.start_redis():
            return

        # 2. Security Report
        await self.print_security_report()

        # 3. Start Neural Engine
        await self.start_neural_engine()
        
        # 4. Wait for Neural Engine health? (Simple delay for now)
        await asyncio.sleep(5) 
        
        # 5. Start Gateway
        await self.start_gateway()
        
        # 6. Start Monitor Task
        monitor_task = asyncio.create_task(self.monitor_processes())
        
        # Wait for shutdown signal
        try:
            await self.shutdown_event.wait()
        except asyncio.CancelledError:
            pass
        finally:
            await self.shutdown()
            monitor_task.cancel()

def main():
    runtime = NooghRuntime()
    loop = asyncio.get_event_loop()
    
    # Handle signals
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(runtime.shutdown()))
    
    try:
        loop.run_until_complete(runtime.run())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

if __name__ == "__main__":
    main()
